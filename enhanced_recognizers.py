"""
Enhanced recognizers module for extending Presidio with additional PII patterns.
This module provides functions to register custom entity recognizers.
"""

import os
from typing import Dict, Any, List
from presidio_analyzer import RecognizerRegistry, PatternRecognizer, Pattern


def register_custom_entities():
    """Register custom enhanced PII entities with the Presidio registry."""
    print("Registering enhanced PII recognizers...")

    # Try to get the current registry from the analyzer
    try:
        # Import here to avoid circular imports
        import pii_presidio

        # Get the current analyzer to access its registry
        analyzer, _ = pii_presidio._get_analyzer()
        registry = analyzer.registry

        # Enhanced US Driver License patterns
        us_driver_license_enhanced = PatternRecognizer(
            supported_entity="US_DRIVER_LICENSE",
            name="enhanced_us_driver_license",
            patterns=[
                # California specific format with higher confidence
                Pattern("ca_dl", r"\bCA\s*[A-Z]\d{7,8}\b", 0.95),
                Pattern("ca_dl_format", r"\b[A-Z]\d{7,8}\b", 0.85),
                # With state prefix
                Pattern("dl_with_state", r"\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\s*[A-Z]\d{6,8}\b", 0.9),
                # With DL prefix
                Pattern("dl_with_prefix", r"\b(?:DL|LICENSE|DRIVER)?\s*#?\s*[A-Z]\d{6,8}\b", 0.9),
            ],
            context=["driver", "license", "driving", "dl", "dln", "identification", "id", "motor vehicle", "dmv", "department of motor", "california"]
        )

        # Enhanced US Passport patterns
        us_passport_enhanced = PatternRecognizer(
            supported_entity="US_PASSPORT",
            name="enhanced_us_passport",
            patterns=[
                # Standard US passport 9-digit format
                Pattern("passport_standard", r"\b\d{9}\b", 0.75),
                # With C prefix (common format)
                Pattern("passport_c_prefix", r"\bC\d{8}\b", 0.95),
                # With passport context
                Pattern("passport_with_context", r"\b(?:PASSPORT|PASSPORT#|TRAVEL)?\s*(?:NO\.?|#)?\s*\d{8,10}\b", 0.9),
                # With US state department patterns
                Pattern("passport_us_format", r"\b[0-9]{6}[0-9]{1,3}\b", 0.6),
            ],
            context=["passport", "travel", "border", "customs", "immigration", "citizenship", "passport#", "us passport", "american passport"]
        )

        # Enhanced IPv6 patterns
        ipv6_enhanced = PatternRecognizer(
            supported_entity="IP_ADDRESS",
            name="enhanced_ipv6",
            patterns=[
                # Full IPv6 patterns
                Pattern("ipv6_full", r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b", 0.98),
                Pattern("ipv6_compressed", r"\b(?:[0-9a-fA-F]{1,4}:)*::(?:[0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{1,4}\b", 0.98),
                Pattern("ipv6_shortened", r"\b(?:[0-9a-fA-F]{1,4}:)*::[0-9a-fA-F]{1,4}\b", 0.95),
                Pattern("ipv6_with_port", r"\b\[?(?:[0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{1,4}\]?(?::\d{1,5})?\b", 0.95),
                # IPv6-mapped IPv4
                Pattern("ipv6_ipv4_mapped", r"\b::ffff:(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", 0.95),
                # Common IPv6 prefixes
                Pattern("ipv6_2001", r"\b2001:(?::[0-9a-fA-F]{0,4}:)*[0-9a-fA-F]{0,4}\b", 0.95),
                Pattern("ipv6_fe80", r"\bfe80::[0-9a-fA-F]{0,4}(:[0-9a-fA-F]{0,4})*\b", 0.95),
            ],
            context=["ip", "address", "network", "server", "host", "connect", "remote", "local", "lan", "wan", "vpn", "ipv6", "tcp", "udp", "protocol"]
        )

        # Enhanced MAC Address patterns
        mac_enhanced = PatternRecognizer(
            supported_entity="MAC_ADDRESS",
            name="enhanced_mac_address",
            patterns=[
                # Standard formats with very high confidence
                Pattern("mac_colons", r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b", 0.99),
                Pattern("mac_hyphens", r"\b(?:[0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}\b", 0.99),
                Pattern("mac_dots", r"\b(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}\b", 0.98),
                # Common variations
                Pattern("mac_mixed_sep", r"\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b", 0.97),
                Pattern("mac_uppercase", r"\b(?:[0-9A-F]{2}:){5}[0-9A-F]{2}\b", 0.98),
            ],
            context=["mac", "address", "hardware", "network", "ethernet", "wifi", "bluetooth", "adapter", "nic", "physical", "interface"]
        )

        # Enhanced Bank Account patterns
        bank_account_enhanced = PatternRecognizer(
            supported_entity="BANK_ACCOUNT",
            name="enhanced_bank_account",
            patterns=[
                Pattern("account_general", r"\b\d{8,17}\b", 0.5),
                Pattern("account_with_prefix", r"\b(?:ACC|ACCOUNT)?\s*#?\s*\d{8,12}\b", 0.92),
                Pattern("routing_with_account", r"\b\d{9}[\s-]+\d{8,12}\b", 0.8),
                Pattern("account_with_context", r"\b(?:ACCOUNT|ACCT|CHECKING|SAVINGS)?\s*(?:NUMBER|#)?\s*[:\s]?\s*\d{8,17}\b", 0.9),
                Pattern("account_long", r"\b\d{12,17}\b", 0.6),
            ],
            context=["account", "bank", "checking", "savings", "routing", "aba", "deposit", "withdraw", "transfer", "wire", "ach"]
        )

        # Enhanced Organization patterns
        organization_enhanced = PatternRecognizer(
            supported_entity="ORGANIZATION",
            name="enhanced_organization",
            patterns=[
                Pattern("org_corp_suffix", r"\b[A-Za-z][A-Za-z\s&]+(?:Corp|Corporation|Inc|Incorporated|LLC|Ltd|Limited|Co|Company|Group|Enterprises|Industries|Solutions|Services|Technologies|International|Global|Worldwide|Systems|Consulting|Associates|Partners|Holdings|Ventures|Studios|Media|Bank|Financial|Insurance|Investments|Securities|Management|Logistics|Transportation|Manufacturing|Retail|Healthcare|Energy|Communications|Construction|Real Estate|Legal|Accounting|Marketing|Advertising|Education|Government|Military)\b", 0.92),
                Pattern("org_the_prefix", r"\bThe\s+[A-Z][a-z]+\s+(?:Company|Corporation|Group|Institute|Foundation|Trust|Association|Agency|Department|Bureau|Office|Center|University|College|School|Hospital|Clinic)\b", 0.85),
                Pattern("org_known_companies", r"\b(?:Microsoft|Google|Apple|Amazon|Meta|Facebook|Tesla|Netflix|Walmart|Toyota|Honda|Ford|GM|Bank of America|Chase|Wells Fargo|Goldman Sachs|Morgan Stanley|IBM|Oracle|Cisco|Intel|NVIDIA|AMD|Qualcomm|Dell|HP|Canon|Epson|Samsung|Sony|Panasonic|Toshiba|Hitachi|Siemens|Philips|Bosch|3M|Caterpillar|Deere|Honeywell|General Electric|Boeing|Lockheed|Raytheon|Northrop|General Dynamics|McDonald's|Burger King|Starbucks|Coca-Cola|Pepsi|Nike|Adidas|Puma|Under Armour|Lululemon|Patagonia|REI|Home Depot|Lowe's|Target|Best Buy|Costco|Walmart|IKEA|Wayfair|Amazon|eBay|Etsy|Uber|Lyft|Airbnb|Booking|Expedia|Marriott|Hilton|Hyatt|Sheraton|Westin|Courtyard|Fairfield|Residence|SpringHill|Hampton|Homewood|Doubletree|Embassy|Holiday Inn|Comfort|Quality|Sleep|Clarion|Econo|MainStay|Super 8|Motel 6|Red Roof|Extended Stay|Candlewood|TownePlace|Staybridge|Element|Delta|American|United|Southwest|JetBlue|Alaska|Hawaiian|Spirit|Frontier|Allegiant|Sun Country|Capital One|Discover|US Bank|PNC|Citibank|Bank of America|Wells Fargo|Chase|Capital One|USAA|Navy Federal|Pentagon|FedEx|UPS|DHL|USPS|Fidelity|Charles Schwab|Vanguard|BlackRock|State Farm|Allstate|Geico|Progressive|Liberty Mutual|American Family|Farmers|Nationwide|Travelers|Chubb|AIG|MetLife|Prudential|New York Life|MassMutual|Northwestern Mutual|TIAA-CREF|Fidelity|Vanguard|Schwab|Merrill Lynch|JPMorgan Chase|Citigroup|Wells Fargo|US Bancorp|PNC|Capital One|American Express|Discover|Visa|Mastercard|PayPal|Stripe|Square|Intuit|TurboTax|H&R Block|Adobe|Salesforce|SAP|Workday|ServiceNow|Atlassian|Zoom|Teams|Slack|Dropbox|Box|AWS|Azure|Google Cloud|IBM Cloud|Oracle Cloud|Salesforce Cloud)\b", 0.96),
            ],
            context=["corp", "company", "inc", "llc", "ltd", "group", "enterprises", "industries", "solutions", "technologies", "international", "global", "worldwide", "systems", "consulting", "associates", "partners", "holdings", "ventures", "studios", "media", "bank", "financial", "insurance", "investments", "securities", "management", "logistics", "transportation", "manufacturing", "retail", "healthcare", "energy", "communications", "construction", "real estate", "legal", "accounting", "marketing", "advertising", "education", "government", "military", "corporation", "business", "organization", "firm", "enterprise", "workplace", "employer"]
        )

        # Indian GSTIN patterns
        indian_gstin_enhanced = PatternRecognizer(
            supported_entity="IN_GSTIN",
            name="indian_gstin_enhanced",
            patterns=[
                # Standard 15-digit GSTIN format: StateCode(2) + PAN(10) + CheckDigit(1) + CheckDigit(1) + Z(1)
                Pattern("gstin_standard", r"\b\d{2}[A-Z]{3}[A-Z0-9]{5}[A-Z0-9]\d[Z][A-Z0-9]\d\b", 0.95),
                Pattern("gstin_with_prefix", r"\b(?:GSTIN|GST|GSTIN:)?\s*\d{2}[A-Z]{3}[A-Z0-9]{5}[A-Z0-9]\d[Z][A-Z0-9]\d\b", 0.9),
                Pattern("gstin_context", r"\b(?:Goods\s+and\s+Services\s+Tax|GST|GSTIN|Tax\s+Identification\s+Number)?\s*(?:No\.?|#)?\s*\d{15}\b", 0.85),
                # Common state codes for GSTIN
                Pattern("gstin_state_specific", r"\b(?:01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|32|33|34|35|36|37|38)[[0-9A-Z]{3}[0-9A-Z]{5}[0-9A-Z]{4}[0-9A-Z]\d[Z][0-9A-Z]\d\b", 0.95),
            ],
            context=["gstin", "gst", "tax", "goods", "services", "identification", "number", "registration", "business", "company", "firma", "organization", "india", "gst portal", "income tax", "vat", "taxable", "compliance"]
        )

        # Indian PAN patterns (Enhanced)
        indian_pan_enhanced = PatternRecognizer(
            supported_entity="IN_PAN",
            name="indian_pan_enhanced",
            patterns=[
                # Enhanced PAN patterns with higher confidence
                Pattern("pan_standard_format", r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", 0.98),
                Pattern("pan_with_card_prefix", r"\b(?:PAN|PANCARD|PAN\s+CARD)?\s*#?\s*[A-Z]{5}[0-9]{4}[A-Z]\b", 0.95),
                Pattern("pan_with_context", r"\b(?:Permanent\s+Account\s+Number|Permanent\s+Account|PAN|PANCARD)?\s*(?:No\.?|#)?\s*[A-Z]{5}[0-9]{4}[A-Z]\b", 0.92),
                Pattern("pan_old_format", r"\b(?:[0-9]{4}[A-Z]{5}[A-Z0-9]{1}[A-Z]\b", 0.8),
                Pattern("pan_new_format", r"\b[A-Z]{3}[P][A-Z][0-9]{4}[A-Z]\b", 0.9),
                # Context-sensitive patterns
                Pattern("pan_tax_related", r"\b(?:PAN\s+No\.|Tax\s+Account\s+No\.|Income\s+Tax\s+PAN|Permanent\s+Account\s+No\.|Unique\s+Identification\s+No\.|UIN)\s*[A-Z]{5}[0-9]{4}[A-Z]\b", 0.95),
                Pattern("pan_financial", r"\b(?:PAN|Tax\s+ID|Bank\s+Account|Investor\s+ID|Demat\s+Account)\s*#?\s*[A-Z]{5}[0-9]{4}[A-Z]\b", 0.9),
                Pattern("pan_business", r"\b(?:PAN|Business\s+Entity|Firm\s+ID|Company\s+Registration)\s*[A-Z]{5}[0-9]{4}[A-Z]\b", 0.85),
            ],
            context=["pan", "tax", "income", "account", "number", "identification", "id", "permanent", "card", "financial", "banking", "demat", "investor", "business", "entity", "firm", "company", "india", "income tax", "assessment", "return", "filing", "itr", "taxable"]
        )

        # Indian Aadhaar patterns (Enhanced)
        indian_aadhaar_enhanced = PatternRecognizer(
            supported_entity="IN_AADHAAR",
            name="indian_aadhaar_enhanced",
            patterns=[
                # Enhanced Aadhaar patterns with improved detection
                Pattern("aadhaar_12_digit", r"\b\d{12}\b", 0.95),
                Pattern("aadhaar_with_spaces", r"\b\d{4}\s\d{4}\s\d{4}\b", 0.9),
                Pattern("aadhaar_with_hyphens", r"\b\d{4}-\d{4}-\d{4}\b", 0.9),
                Pattern("aadhaar_verification", r"\b(?:AADHAAR|Aadhaar|Aadhaar\s+No\.|Aadhaar\s+Card|Aadhaar\s+Number|Aadhaar\s+ID|UIDAI|Unique\s+Identification\s+Authority\s+of\s+India)\s*(?:No\.?|#)?\s*\d{12}\b", 0.98),
                Pattern("aadhaar_kyc", r"\b(?:KYC|Know\s+Your\s+Customer|Identity\s+Verification|Customer\s+Identification)\s*(?:Aadhaar|Aadhaar\s+No\.)\s*\d{12}\b", 0.95),
                Pattern("aadhaar_government", r"\b(?:UID|UIDAI|Unique\s+ID|Citizen\s+ID|National\s+ID)\s*(?:No\.?|#)?\s*\d{12}\b", 0.9),
                Pattern("aadhaar_digital", r"\b(?:e-Aadhaar|Digital\s+Aadhaar|Virtual\s+Aadhaar)\s*(?:No\.?|#)?\s*\d{12}\b", 0.88),
                Pattern("aadhaar_mobile", r"\b(?:Mobile\s+Aadhaar|Aadhaar\s+Link|Phone\s+Aadhaar)\s*(?:No\.?|#)?\s*\d{12}\b", 0.85),
            ],
            context=["aadhaar", "uidai", "identification", "id", "kyc", "verification", "government", "citizen", "national", "digital", "mobile", "linking", "unique", "india", "biometric", "biometric"]
        )

        # Indian Passport patterns (Enhanced)
        indian_passport_enhanced = PatternRecognizer(
            supported_entity="IN_PASSPORT",
            name="indian_passport_enhanced",
            patterns=[
                # Standard Indian passport format: P + 7 digits + 1 digit
                Pattern("passport_standard", r"\bP\d{7}[A-Z]\b", 0.95),
                Pattern("passport_with_prefix", r"\b(?:PASSPORT|PASSPORT#|INDIAN\s+PASSPORT|INDIA\s+PASSPORT)?\s*(?:NO\.?|#)?\s*[P]\d{7}[A-Z]\b", 0.9),
                Pattern("passport_with_context", r"\b(?:Passport\s+No\.|Indian\s+Passport|Travel\s+Document|Immigration\s+Document)\s*[P]\d{7}[A-Z]\b", 0.85),
                Pattern("passport_official", r"\b(?:Official\s+Passport|Government\s+ID|Ministry\s+of\s+External\s+Affairs)\s*[P]\d{7}[A-Z]\b", 0.88),
                Pattern("passport_renewal", r"\b(?:Renewal\s+Passport|Passport\s+Renewal|Passport\s+Application)\s*[P]\d{7}[A-Z]\b", 0.85),
                Pattern("passport_diplomatic", r"\b(?:Diplomatic\s+Passport|Official\s+Travel\s+Document|Consular\s+Services)\s*[P]\d{7}[A-Z]\b", 0.9),
            ],
            context=["passport", "travel", "india", "immigration", "consular", "embassy", "ministry", "external", "affairs", "government", "official", "document", "identification", "citizenship"]
        )

        # Register all enhanced recognizers
        recognizers_to_add = [
            ("enhanced_us_driver_license", us_driver_license_enhanced),
            ("enhanced_us_passport", us_passport_enhanced),
            ("enhanced_ipv6", ipv6_enhanced),
            ("enhanced_mac_address", mac_enhanced),
            ("enhanced_bank_account", bank_account_enhanced),
            ("enhanced_organization", organization_enhanced),
            ("indian_gstin_enhanced", indian_gstin_enhanced),
            ("indian_pan_enhanced", indian_pan_enhanced),
            ("indian_aadhaar_enhanced", indian_aadhaar_enhanced),
            ("indian_passport_enhanced", indian_passport_enhanced)
        ]

        for name, recognizer in recognizers_to_add:
            try:
                registry.add_recognizer(recognizer)
                print(f"Successfully registered enhanced recognizer: {name}")
            except Exception as e:
                print(f"Failed to register enhanced recognizer {name}: {e}")

        print("Enhanced PII recognizers registration completed")

    except Exception as e:
        print(f"Error registering enhanced recognizers: {e}")
        # Continue without enhanced recognizers if registration fails


def get_available_enhanced_entities() -> List[str]:
    """Get a list of available enhanced entity types."""
    return [
        "US_DRIVER_LICENSE",
        "US_PASSPORT",
        "IP_ADDRESS",
        "MAC_ADDRESS",
        "BANK_ACCOUNT",
        "ORGANIZATION",
        "IN_GSTIN",
        "IN_PAN",
        "IN_AADHAAR",
        "IN_PASSPORT"
    ]