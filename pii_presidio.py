import os, re
from typing import List, Dict, Any, Optional, Tuple
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern, RecognizerResult
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import custom_config

_analyzer: Optional[AnalyzerEngine] = None
_anonymizer: Optional[AnonymizerEngine] = None

def _build_recognizers(registry: RecognizerRegistry):
    # India Aadhaar (12 digits, with optional spaces) - ENHANCED
    aadhaar = PatternRecognizer(
        supported_entity="IN_AADHAAR",
        name="aadhaar_pattern",
        patterns=[
            # ENHANCED Aadhaar patterns with improved detection
            Pattern("aadhaar_12_digit", r"\b\d{12}\b", 0.95),
            Pattern("aadhaar_with_spaces", r"\b\d{4}\s\d{4}\s\d{4}\b", 0.9),
            Pattern("aadhaar_with_hyphens", r"\b\d{4}-\d{4}-\d{4}\b", 0.9),
            Pattern("aadhaar_verification", r"\b(?:AADHAAR|Aadhaar|Aadhaar\s+No\.|Aadhaar\s+Card|Aadhaar\s+Number|Aadhaar\s+ID|UIDAI|Unique\s+Identification\s+Authority\s+of\s+India)\s*(?:No\.?|#)?\s*\d{12}\b", 0.98),
            Pattern("aadhaar_kyc", r"\b(?:KYC|Know\s+Your\s+Customer|Identity\s+Verification|Customer\s+Identification)\s*(?:Aadhaar|Aadhaar\s+No\.)\s*\d{12}\b", 0.95),
            Pattern("aadhaar_government", r"\b(?:UID|UIDAI|Unique\s+ID|Citizen\s+ID|National\s+ID)\s*(?:No\.?|#)?\s*\d{12}\b", 0.9),
        ],
        context=["aadhaar", "uidai", "identification", "id", "kyc", "verification", "government", "citizen", "national", "digital", "mobile", "linking", "unique", "india", "biometric"]
    )
    # India PAN (5 letters + 4 digits + 1 letter)
    pan = PatternRecognizer(
        supported_entity="IN_PAN",
        name="pan_pattern",
        patterns=[Pattern("pan", r"\b[A-Z]{5}\d{4}[A-Z]\b", 0.6)],
    )
    # India Passport (simple common form: letter + 7 digits, excluding some letters)
    in_passport = PatternRecognizer(
        supported_entity="IN_PASSPORT",
        name="in_passport_pattern",
        patterns=[Pattern("in_passport", r"\b[A-PR-WY][1-9]\d{6}\b", 0.5)],
    )
    # Custom SSN recognizer with improved patterns - ENHANCED
    ssn = PatternRecognizer(
        supported_entity="US_SSN",
        name="custom_ssn_pattern",
        patterns=[
            # MAXIMUM CONFIDENCE PATTERNS (1.0) - Cannot be overridden
            Pattern("ssn_with_dashes", r"\b\d{3}-\d{2}-\d{4}\b", 1.0),
            Pattern("ssn_with_spaces", r"\b\d{3} \d{2} \d{4}\b", 1.0),
            Pattern("ssn_with_number_sign", r"\b(?:SSN|Social\s+Security)\s*#?\s*\d{3}-\d{2}-\d{4}\b", 1.0),

            # HIGH-CONFIDENCE CONTEXT-AWARE PATTERNS (0.95-0.98)
            Pattern("ssn_with_context", r"\b(?:Social\s+Security\s+Number|SSN|Social\s+Security)\s*(?:No\.?|#)?\s*\d{3}-\d{2}-\d{4}\b", 0.98),
            Pattern("ssn_employee_context", r"\b(?:Employee|Worker|Staff|Personnel)\s+(?:ID|Identification|SSN|Social)\s*#?\s*\d{3}-\d{2}-\d{4}\b", 0.95),
            Pattern("ssn_for_employment", r"\b(?:Employment|Background|Check|Verification)\s+(?:SSN|Social)\s*#?\s*\d{3}-\d{2}-\d{4}\b", 0.95),
            Pattern("ssn_with_parens", r"\b(?:SSN|Social)\s*(?:#)?\s*\(?\d{3}\)?[-.\s]?\d{2}[-.\s]?\d{4}\b", 0.95),

            # MEDIUM-CONFIDENCE PATTERNS (0.8-0.9) - With partial context
            Pattern("ssn_continuous_9", r"\b\d{9}\b", 0.5),  # Increased from 0.3 to 0.5
            Pattern("ssn_tax_context", r"\b(?:Tax|W-2|W2|IRS|Income\s+Tax)\s+(?:ID|SSN|Social)\s*#?\s*\d{3}-\d{2}-\d{4}\b", 0.9),
            Pattern("ssn_benefits", r"\b(?:Benefits|Retirement|Disability|Medicare|Social\s+Security)\s+(?:ID|Number|#)?\s*\d{3}-\d{2}-\d{4}\b", 0.9),
        ],
        context=["social", "security", "ssn", "ssns", "ssn#", "ss#", "ssid", "social security", "identification", "employee", "tax", "benefits", "retirement", "disability", "medicare", "income tax", "w-2", "w2", "irs"]
    )
    # Custom Credit Card recognizer with improved patterns
    cc = PatternRecognizer(
        supported_entity="CREDIT_CARD",
        name="custom_cc_pattern",
        patterns=[
            Pattern("cc_with_dashes", r"\b\d{4}-\d{4}-\d{4}-\d{4}\b", 0.8),
            Pattern("cc_with_spaces", r"\b\d{4} \d{4} \d{4} \d{4}\b", 0.8),
            Pattern("cc_continuous", r"\b\d{16}\b", 0.3)  # Lower score for continuous digits
        ],
        context=["credit", "card", "visa", "mastercard", "cc", "amex", "discover", "jcb", "diners", "maestro", "instapayment"]
    )
    # Custom Phone Number recognizer with improved patterns
    phone = PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        name="custom_phone_pattern",
        patterns=[
            Pattern("phone_with_plus", r"\+\d{1}-\d{3}-\d{3}-\d{4}\b", 0.8),
            Pattern("phone_with_dashes", r"\b\d{3}-\d{3}-\d{4}\b", 0.8),
            Pattern("phone_with_spaces", r"\b\d{3} \d{3} \d{4}\b", 0.8),
            Pattern("phone_with_parens", r"\(\d{3}\)\s?\d{3}-\d{4}\b", 0.8)
        ],
        context=["call", "phone", "telephone", "tel", "mobile"]
    )
    # IP Address recognizer - DISABLED to prevent conflicts with medical, address, and financial patterns
    # The IP address detection was causing excessive false positives on:
    # - Medical IDs (AETNA-8842-77B → IP_ADDRESS instead of MEDICAL_ID)
    # - Street addresses (1550 Tech Circle → IP_ADDRESS instead of LOCATION)
    # - Date components (11/05/2003 → IP_ADDRESS instead of DATE_OF_BIRTH)
    # - Project codes (PROJ-8872-AD → IP_ADDRESS instead of PROJECT_CODE)
    # - Expiration dates (Exp. 08/27 → IP_ADDRESS instead of EXPIRATION_DATE)
    # ip_address = None  # DISABLED - RE-ENABLE ONLY IF SPECIFIC IP DETECTION IS NEEDED
    # MAC Address recognizer - BOOSTED TO 1.0 CONFIDENCE
    mac_address = PatternRecognizer(
        supported_entity="MAC_ADDRESS",
        name="mac_address_pattern",
        patterns=[
            # MAXIMUM CONFIDENCE PATTERNS (1.0) - Cannot be overridden
            Pattern("mac_with_colons", r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b", 1.0),
            Pattern("mac_with_hyphens", r"\b(?:[0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}\b", 1.0),
            Pattern("mac_uppercase", r"\b(?:[0-9A-F]{2}:){5}[0-9A-F]{2}\b", 1.0),
            Pattern("mac_mixed", r"\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b", 1.0),

            # VERY HIGH CONFIDENCE PATTERNS (0.99)
            Pattern("mac_with_dots", r"\b(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}\b", 0.99),
            Pattern("mac_with_spaces", r"\b(?:[0-9A-Fa-f]{2}\s){5}[0-9A-Fa-f]{2}\b", 0.99)
        ],
        context=["mac", "address", "hardware", "network", "ethernet", "wifi", "bluetooth", "adapter", "nic", "physical address"]
    )
    # Bank Account Number recognizer - ENHANCED WITH CONTEXT AWARENESS
    bank_account = PatternRecognizer(
        supported_entity="BANK_ACCOUNT",
        name="bank_account_pattern",
        patterns=[
            # HIGH-CONFIDENCE CONTEXT-AWARE PATTERNS (0.95) - Only with explicit context
            Pattern("account_with_context", r"\b(?:ACCOUNT|ACCT|CHECKING|SAVINGS)\s*(?:NUMBER|#)?\s*[:\s]?\s*\d{8,17}\b", 0.95),
            Pattern("account_with_prefix", r"\b(?:ACC|ACCOUNT)?\s*#?\s*\d{8,12}\b", 0.95),
            Pattern("bank_with_account", r"\b(?:BANK|FINANCIAL)\s*(?:ACCOUNT|ACCT)?\s*#?\s*\d{8,17}\b", 0.95),

            # MEDIUM-CONFIDENCE PATTERNS (0.8-0.9) - With partial context
            Pattern("routing_with_account", r"\b\d{9}[\s-]+\d{8,12}\b", 0.85),  # Routing + Account
            Pattern("account_with_colon", r"\b(?:ACCOUNT|ACCT)\s*[:#]\s*\d{8,17}\b", 0.9),
            Pattern("savings_checking", r"\b(?:SAVINGS|CHECKING)\s*(?:ACCOUNT)?\s*#?\s*\d{8,17}\b", 0.9),

            # EXCLUSION PATTERNS - AVOID PHONE NUMBERS (0.1) - Very low confidence to override
            Pattern("account_deposit_context", r"\b(?:DEPOSIT|DIRECT|WIRE|TRANSFER|ACH)\s*(?:TO)?\s*[:\s]?[0-9]{8,17}\b", 0.9),
            Pattern("account_number_only", r"\b(?:ACCOUNT\s*(?:NUMBER|#)\s*[:#]?\s*|[A-Z]{3,8}\s*ACCOUNT|#\s*)[0-9]{8,17}\b", 0.95),
            Pattern("avoid_phone_format", r"\b(?![(]?[0-9]{3}[)]?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b)[0-9]{10}\b", 0.7)
        ],
        context=["account", "bank", "checking", "savings", "routing", "aba", "deposit", "withdraw", "balance", "transfer", "wire", "direct deposit"]
    )
    # Bank Routing Number recognizer (US ABA routing numbers) - ENHANCED
    bank_routing = PatternRecognizer(
        supported_entity="BANK_ROUTING",
        name="bank_routing_pattern",
        patterns=[
            # HIGH-CONFIDENCE ROUTING PATTERNS (0.95) - Strong context required
            Pattern("routing_with_context", r"\b(?:RT|RTN|ABA|ROUTING)?\s*#?\s*\d{9}\b", 0.95),
            Pattern("routing_for_transfer", r"\b(?:WIRE|TRANSFER|ACH|DIRECT)?\s*DEPOSIT?\s*(?:TO)?\s*[:\s]?\s*\d{9}\b", 0.9),
            Pattern("routing_bank_context", r"\b(?:BANK|CHASE|WELLS|BOA|BANK\s+OF\s+AMERICA|CITI|CAPITAL\s+ONE)\s+(?:ROUTING|ABA|RT|RTN)?\s*#?\s*:?\s*\d{9}\b", 0.95),

            # MEDIUM-CONFIDENCE PATTERNS (0.7-0.8) - Some context
            Pattern("routing_with_check", r"\b\d{9}[\s-]+\d{6,10}\b", 0.5),  # Found with check number
            Pattern("routing_for_ach", r"\b(?:ACH|ELECTRONIC|DIRECT)\s+(?:DEPOSIT|TRANSFER|PAYMENT)\s*(?:TO)?\s*[:#]?\s*\d{9}\b", 0.85),

            # EXCLUSION PATTERNS - LOW CONFIDENCE TO OVERRIDE SSN (0.1-0.2)
            Pattern("avoid_ssn_format", r"(?<!\b(?:SOCIAL\s+SECURITY|SSN|SSNS|SSID)\s*(?:NUMBER|#)?\s*[:#]?\s*)\b\d{3}-\d{2}-\d{4}\b", 0.1),  # Exclude SSN format
            Pattern("routing_only_with_bank", r"\b(?:BANK|FINANCIAL)\s+(?:ROUTING|ABA|TRANSIT)\s+(?:NUMBER|#)?\s*[:#]?\s*\d{9}\b", 0.95),
            Pattern("exclude_valid_ssn", r"^(?!.*(?:SOCIAL|SSN|SS#|SSID)).*\b\d{9}\b", 0.2)  # Negative lookahead for SSN context
        ],
        context=["routing", "aba", "rt", "rtn", "bank", "transit", "wire", "transfer", "ach", "deposit", "electronic", "direct deposit", "check"]
    )
    # US Driver License recognizer - ENHANCED PATTERNS
    us_driver_license = PatternRecognizer(
        supported_entity="US_DRIVER_LICENSE",
        name="us_driver_license_pattern",
        patterns=[
            # HIGH-CONFIDENCE STATE-SPECIFIC PATTERNS (0.99)
            Pattern("dl_with_state", r"\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)[A-Z]\d{6,7}\b", 0.99),
            Pattern("dl_california", r"\bCA\s*[A-Z]\d{7}\b", 0.99),
            Pattern("dl_texas", r"\bTX\s*[0-9]{7,8}\b", 0.99),
            Pattern("dl_florida", r"\bFL\s*[A-Z]\d{12,13}\b", 0.99),

            # CONTEXT-AWARE PATTERNS (0.95)
            Pattern("dl_with_prefix", r"\b(?:DL|LICENSE|DRIVER)\s*#?\s*[A-Z]\d{6,8}\b", 0.95),
            Pattern("dl_with_permit", r"\b(?:PERMIT|ID)\s*#?\s*[A-Z]\d{6,8}\b", 0.95),
            Pattern("dl_state_with_context", r"\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\s*\d{7,8}\b", 0.95),

            # LOWER-CONFIDENCE GENERAL PATTERNS (0.6-0.7)
            Pattern("dl_general", r"\b[A-Z]\d{7,8}\b", 0.7),  # General format: 1 letter + 7-8 digits
            Pattern("dl_with_spaces", r"\b[A-Z]\s*\d{7,8}\b", 0.6)  # With spaces
        ],
        context=["driver", "license", "dl", "driving", "license#", "permit", "id", "identification", "state id", "driver's license", "driver license"]
    )
    # US Passport recognizer - ENHANCED PATTERNS
    us_passport = PatternRecognizer(
        supported_entity="US_PASSPORT",
        name="us_passport_pattern",
        patterns=[
            # MAXIMUM CONFIDENCE C-PREFIX PATTERNS (0.99)
            Pattern("passport_c_prefix", r"\bC\d{8,9}\b", 0.99),  # C-prefixed passports
            Pattern("passport_us_prefix", r"\b[0-9]{9}\b", 0.3),  # Lower confidence for generic 9-digit

            # HIGH-CONFIDENCE CONTEXT-AWARE PATTERNS (0.95)
            Pattern("passport_with_context", r"\b(?:PASSPORT|PASSPORT#|TRAVEL)\s*(?:NO\.?|#)?\s*\d{8,10}\b", 0.95),
            Pattern("passport_us_context", r"\bU\.?S\.?\s*PASSPORT\s*(?:NO\.?|#)?\s*\d{8,10}\b", 0.95),
            Pattern("passport_booklet", r"\bPASSPORT\s*(?:BOOKLET|ID)\s*[:#]?\s*\d{6,10}\b", 0.95),

            # MEDIUM CONFIDENCE PATTERNS (0.7-0.8)
            Pattern("passport_application", r"\b(?:APPLICATION|FORM)\s*[A-Z]?\s*#\s*\d{6,10}\b", 0.8),
            Pattern("passport_renewal", r"\b(?:RENEWAL|EXPIRATION|ISSUE)\s*(?:DATE|NO)\s*[:#]?\s*\d{6,10}\b", 0.7)
        ],
        context=["passport", "travel", "border", "customs", "immigration", "citizenship", "passport#", "us passport", "american passport", "travel document"]
    )
    # Date of Birth recognizer - MEDICAL CONTEXT AWARE
    date_of_birth = PatternRecognizer(
        supported_entity="DATE_OF_BIRTH",
        name="date_of_birth_pattern",
        patterns=[
            # HIGH-CONFIDENCE PATTERNS (0.95) - With explicit medical/birth context
            Pattern("dob_with_context", r"\b(?:DOB|Date\s+of\s+Birth|Birth\s+Date|Born)\s*[:\-]?\s*\d{2}[-/]\d{2}[-/]\d{4}\b", 0.95),
            Pattern("dob_patient_context", r"\b(?:Patient|Client|Individual)\s*(?:DOB|Birth)\s*[:\-]?\s*\d{2}[-/]\d{2}[-/]\d{4}\b", 0.95),
            Pattern("dob_age_context", r"\b(?:Age|aged)\s+\d+[,]?\s*(?:born|DOB|birth\s+date)\s*[:\-]?\s*\d{2}[-/]\d{2}[-/]\d{4}\b", 0.9),

            # MEDIUM-CONFIDENCE PATTERNS (0.7-0.8) - Date format with partial context
            Pattern("dob_mdy_format", r"\b(?<!\(\d{3}\)\s*[-.]\s*?)\d{2}[-/]\d{2}[-/]\d{4}\b(?![:\-]\s*\d{4})", 0.7),
            Pattern("dob_parentheses", r"\b\(\d{2}[-/]\d{2}[-/]\d{4}\)\b(?!(?:[-\s]*\d{4}|\s*ending|\s*card))", 0.75),
            Pattern("dob_explicit", r"\b(?:birth|born)\s+(?:on|at|in)\s+\d{2}[-/]\d{2}[-/]\d{4}\b", 0.8),

            # EXCLUSION PATTERNS (0.1) - Very low confidence to avoid phone detection
            Pattern("dob_exclude_phone", r"(?<!\(\d{3}\)\s*[-.]\s*)\d{2}[-/]\d{2}[-/]\d{4}\b", 0.1)
        ],
        context=["dob", "birth", "born", "patient", "client", "individual", "age", "medical", "health", "date", "birthday"]
    )
    # Enhanced Credit Card recognizer - BETTER SHORT FORMAT DETECTION
    credit_card_enhanced = PatternRecognizer(
        supported_entity="CREDIT_CARD_ENHANCED",
        name="credit_card_enhanced_pattern",
        patterns=[
            # MAXIMUM CONFIDENCE PATTERNS (1.0) - Full 16-digit credit cards
            Pattern("cc_16_digits", r"\b(?:\d{4}[-\s]){3}\d{4}\b", 1.0),
            Pattern("cc_with_spaces", r"\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b", 1.0),

            # HIGH-CONFIDENCE CONTEXT-AWARE PATTERNS (0.95) - Credit card context
            Pattern("cc_with_context", r"\b(?:Credit|Debit|ATM|Gift)\s*Card\s*(?:Number|#)?\s*[:\-]?\s*\d{4,16}\b", 0.95),
            Pattern("cc_ending_format", r"\b(?:card|account)\s*(?:ending|last\s+4|expiring|expires)\s*(?:in)?\s*[:\-]?\s*\d{4}\b", 0.95),

            # MEDIUM-CONFIDENCE PATTERNS (0.85-0.9) - Partial credit card detection
            Pattern("cc_amex_format", r"\b(?:Amex|American\s+Express?|AE)\s*(?:card|account)?\s*(?:ending|expiring)?\s*[:\-]?\s*\d{4}\b", 0.9),
            Pattern("cc_short_with_payment", r"\b(?:payment|charge|transaction|purchase)\s*(?:made|paid|with|using)\s*(?:card|Amex|Visa|Mastercard)\s*[:\-]?\s*\d{4}\b", 0.85),
            Pattern("cc_security_code", r"\b(?:CVV|CVC|Security\s+Code|PIN)\s*[:\-]?\s*\d{3,4}\b", 0.8),

            # EXCLUSION PATTERNS (0.2-0.3) - Avoid false positives in non-credit contexts
            Pattern("cc_exclude_year", r"\b(?:20|19)\d{2}\b(?!(?:[-\s]*card|[-\s]*expiring|[-\s]*ending))", 0.2)
        ],
        context=["credit", "card", "debit", "visa", "mastercard", "amex", "discover", "jcb", "diners", "maestro", "payment", "charge", "transaction", "purchase", "atm", "gift", "banking", "financial"]
    )
    # Medical/Insurance ID recognizer - HEALTHCARE CONTEXT AWARE
    medical_id = PatternRecognizer(
        supported_entity="MEDICAL_ID",
        name="medical_id_pattern",
        patterns=[
            # HIGH-CONFIDENCE PATTERNS (0.95) - Explicit medical/insurance context
            Pattern("member_id_insurance", r"\b(?:Member\s+ID|Patient\s+ID|MRN|Medical\s+Record|Patient\s+Account)\s*[:\-]?\s*[A-Z]{2,6}[-\s]*\d{4,10}[-\s]*[A-Z0-9]{2,6}\b", 0.95),
            Pattern("insurance_provider", r"\b(?:AETNA|Blue\s+Cross|United|Cigna|Humana|Kaiser|Anthem|WellPoint|Medicare|Medicaid)\s*[-:]?\s*[A-Z0-9]{6,12}\b", 0.95),
            Pattern("policy_number", r"\b(?:Policy|Policy\s+Number|Plan|Group\s+Number)\s*[:\-]?\s*[A-Z0-9]{6,15}\b", 0.9),

            # MEDIUM-CONFIDENCE PATTERNS (0.8-0.9) - Healthcare context
            Pattern("healthcare_id", r"\b(?:Health|Medical|Dental|Vision|Pharmacy)\s*(?:Plan|Coverage|Insurance|Benefits)\s*ID\s*[:\-]?\s*[A-Z0-9]{6,12}\b", 0.85),
            Pattern("subscriber_id", r"\b(?:Subscriber|Member|Patient|Dependent)\s*(?:ID|Number|Account)\s*[:\-]?\s*[A-Z0-9]{6,12}\b", 0.8),

            # PATTERN VARIATIONS (0.75-0.85) - Different formats
            Pattern("member_id_formats", r"\b[A-Z]{2,8}[-\s]*\d{4,10}[-\s]*[A-Z0-9]{2,4}\b", 0.75),
            Pattern("medical_id_generic", r"\b[A-Z0-9]{8,20}\b", 0.4),  # Lower confidence for generic alphanumeric IDs

            # EXCLUSION PATTERNS (0.1) - Avoid false positives
            Pattern("exclude_tracking", r"(?<!\b(?:Tracking|Reference|Case|File|Ticket|Order)\s*(?:Number|#)\s*[:\-]?\s*)[A-Z0-9]{8,20}\b", 0.1),
        ],
        context=["medical", "health", "healthcare", "insurance", "patient", "member", "subscriber", "policy", "plan", "coverage", "benefits", "pharmacy", "dental", "vision", "hospital", "clinic", "doctor", "aetna", "medicare", "medicaid"]
    )
    # Organization recognizer
    organization = PatternRecognizer(
        supported_entity="ORGANIZATION",
        name="organization_pattern",
        patterns=[
            Pattern("org_corp_suffix", r"\b[A-Za-z][A-Za-z\s&]+(?:Corp|Corporation|Inc|Incorporated|LLC|Ltd|Limited|Co|Company|Group|Enterprises|Industries|Solutions|Services|Technologies|International|Global|Worldwide|Systems|Consulting|Associates|Partners|Holdings|Ventures|Studios|Media|Bank|Financial|Insurance|Investments|Securities|Management|Logistics|Transportation|Manufacturing|Retail|Healthcare|Energy|Communications|Construction|Real Estate|Legal|Accounting|Marketing|Advertising|Education|Government|Military)\b", 0.9),
            Pattern("org_the", r"\bThe\s+[A-Z][a-z]+\s+(?:Company|Corporation|Group|Institute|Foundation|Trust|Association|Agency|Department|Bureau|Office|Center|University|College|School|Hospital|Clinic)\b", 0.8),
            Pattern("org_known_companies", r"\b(?:Microsoft|Google|Apple|Amazon|Meta|Facebook|Tesla|Netflix|Walmart|Toyota|Honda|Ford|GM|Bank of America|Chase|Wells Fargo|Goldman Sachs|Morgan Stanley|IBM|Oracle|Cisco|Intel|NVIDIA|AMD|Qualcomm|Dell|HP|Canon|Epson|Samsung|Sony|Panasonic|Toshiba|Hitachi|Siemens|Philips|Bosch|3M|Caterpillar|Deere|Honeywell|General Electric|Boeing|Lockheed|Raytheon|Northrop|General Dynamics|McDonald's|Burger King|Starbucks|Coca-Cola|Pepsi|Nike|Adidas|Puma|Under Armour|Lululemon|Patagonia|REI|Home Depot|Lowe's|Target|Best Buy|Costco|Walmart|IKEA|Wayfair|Amazon|eBay|Etsy|Uber|Lyft|Airbnb|Booking|Expedia|Marriott|Hilton|Hyatt|Marriott|Hilton|Sheraton|Westin|Courtyard|Fairfield|Residence|SpringHill|Hampton|Homewood|Doubletree|Embassy|Holiday Inn|Comfort|Quality|Sleep|Clarion|Econo|MainStay|Super 8|Motel 6|Red Roof|Extended Stay|Candlewood|TownePlace|Staybridge|Element|Residence Inn by Marriott|SpringHill Suites by Marriott|Fairfield by Marriott|Courtyard by Marriott|Sheraton by Marriott|Westin by Marriott|JW Marriott|Autograph Collection|Marriott Bonvoy|Delta|American|United|Southwest|JetBlue|Alaska|Hawaiian|Spirit|Frontier|Allegiant|Sun Country|Capital One|Discover|US Bank|PNC|Citibank|Bank of America|Wells Fargo|Chase|Capital One|USAA|Navy Federal|Pentagon|FedEx|UPS|DHL|USPS|USPS|Fidelity|Charles Schwab|Vanguard|BlackRock|State Farm|Allstate|Geico|Progressive|Liberty Mutual|American Family|Farmers|Nationwide|Travelers|Chubb|AIG|MetLife|Prudential|New York Life|MassMutual|Northwestern Mutual|TIAA-CREF|Fidelity|Vanguard|Schwab|Merrill Lynch|Bank of America|Morgan Stanley|Goldman Sachs|JPMorgan Chase|Citigroup|Wells Fargo|US Bancorp|PNC|Capital One|American Express|Discover|Visa|Mastercard|PayPal|Stripe|Square|Intuit|TurboTax|H&R Block|Adobe|Microsoft|Oracle|Salesforce|SAP|Workday|ServiceNow|Atlassian|Zoom|Teams|Slack|Dropbox|Box|Google|Microsoft Office|Office 365|Windows Server|Linux|AWS|Azure|Google Cloud|Azure|IBM Cloud|Oracle Cloud|Salesforce Cloud)\b", 0.95)
        ],
        context=["corp", "company", "inc", "llc", "ltd", "group", "enterprises", "industries", "solutions", "technologies", "international", "global", "worldwide", "systems", "consulting", "associates", "partners", "holdings", "ventures", "studios", "media", "bank", "financial", "insurance", "investments", "securities", "management", "logistics", "transportation", "manufacturing", "retail", "healthcare", "energy", "communications", "construction", "real estate", "legal", "accounting", "marketing", "advertising", "education", "government", "military"]
    )
    # Add recognizers with error handling to prevent cascade failures
    # IP_ADDRESS DISABLED to prevent conflicts with medical, address, and financial patterns
    recognizers_to_add = [
        ("aadhaar", aadhaar),
        ("pan", pan),
        ("in_passport", in_passport),
        ("ssn", ssn),
        ("cc", cc),
        ("phone", phone),
        # ("ip_address", ip_address),  # DISABLED - causing conflicts with other recognizers
        ("mac_address", mac_address),
        ("bank_account", bank_account),
        ("bank_routing", bank_routing),
        ("us_driver_license", us_driver_license),
        ("us_passport", us_passport),
        ("date_of_birth", date_of_birth),
        ("credit_card_enhanced", credit_card_enhanced),
        ("medical_id", medical_id),
        ("organization", organization)
    ]

    for name, recognizer in recognizers_to_add:
        try:
            registry.add_recognizer(recognizer)
            print(f"Successfully loaded custom recognizer: {name}")
        except Exception as e:
            print(f"Failed to load custom recognizer {name}: {e}")
            # Continue loading other recognizers instead of failing completely

    # Load custom entities
    _load_custom_entities(registry)

def _load_custom_entities(registry: RecognizerRegistry):
    """Load custom entities from configuration files"""
    try:
        custom_entities = custom_config.load_custom_entities()
        for entity in custom_entities:
            if entity.get("pattern"):
                # Create a custom pattern recognizer
                recognizer = PatternRecognizer(
                    supported_entity=entity["type"],
                    name=f"custom_{entity['type'].lower()}",
                    patterns=[Pattern(entity["type"], entity["pattern"], 0.9)],
                    context=entity.get("context", [])
                )
                registry.add_recognizer(recognizer)
                print(f"Loaded custom entity: {entity['type']} with pattern: {entity['pattern']}")
    except Exception as e:
        print(f"Error loading custom entities: {e}")

def _get_analyzer() -> Tuple[AnalyzerEngine, AnonymizerEngine]:
    global _analyzer, _anonymizer
    if _analyzer and _anonymizer:
        return _analyzer, _anonymizer

    lang = os.getenv("PRESIDIO_LANGUAGE", "en")
    spacy_model = os.getenv("SPACY_MODEL", "en_core_web_sm")

    nlp_engine = SpacyNlpEngine(models={lang: spacy_model})
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()

    # Remove conflicting default recognizers that cause incorrect detections
    conflicting_recognizers = [
        "PHONE_NUMBER",  # Conflicts with our bank account detection
        # "US_SSN",        # Keep default SSN to avoid conflicts with our enhanced version
        "IP_ADDRESS",    # Conflicts with our MAC address and year detection
    ]

    # Remove conflicting recognizers FIRST, then add our enhanced ones
    for recognizer_name in conflicting_recognizers:
        try:
            registry.remove_recognizer(recognizer_name)
            print(f"Removed conflicting default recognizer: {recognizer_name}")
        except Exception as e:
            print(f"Could not remove recognizer {recognizer_name}: {e}")

    _build_recognizers(registry)

    _analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
    _anonymizer = AnonymizerEngine()
    return _analyzer, _anonymizer

def reset_analyzer_cache():
    """Reset the global analyzer and anonymizer cache to force rebuild with new recognizers."""
    global _analyzer, _anonymizer
    _analyzer = None
    _anonymizer = None
    print("Analyzer cache reset - will rebuild with new recognizers on next request")

def analyze_presidio(
    text: str,
    language: str,
    entities: Optional[List[str]],
    global_threshold: float,
    per_entity_threshold: Dict[str, float],
) -> List[RecognizerResult]:
    analyzer, _ = _get_analyzer()
    results = analyzer.analyze(
        text=text,
        language=language,
        entities=entities,
        score_threshold=min(0.01, global_threshold),  # run loose, filter below
    )
    out: List[RecognizerResult] = []
    for r in results:
        th = per_entity_threshold.get(r.entity_type, global_threshold)
        if (r.score or 0) >= th:
            out.append(r)
    return out

def anonymize_presidio(text: str, results: List[RecognizerResult], placeholders: Dict[str, str]) -> str:
    _, anonymizer = _get_analyzer()
    ops = {}
    default_token = placeholders.get("DEFAULT", "[REDACTED]")

    def tok(ent, default):
        return placeholders.get(ent, placeholders.get(ent.upper(), default))

    for r in results:
        ent = r.entity_type
        ops[ent] = OperatorConfig("replace", {"new_value": tok(ent, default_token)})
    ops["DEFAULT"] = OperatorConfig("replace", {"new_value": default_token})

    result = anonymizer.anonymize(text=text, analyzer_results=results, anonymizers_config=ops)
    return result.text