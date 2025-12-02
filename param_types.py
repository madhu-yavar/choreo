import re
import phonenumbers
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from cucumber_expressions.parameter_type import ParameterType

EMAIL_RE = r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
UUID_RE  = r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}"
DATE_ISO = r"\d{4}-\d{2}-\d{2}"
TIME_ISO = r"\d{2}:\d{2}(?::\d{2})?"
URL_RE   = r"https?://[^\s]+"
AADHAAR  = r"\d{4}\s?\d{4}\s?\d{4}"
PAN      = r"[A-Z]{5}\d{4}[A-Z]"

# Enhanced patterns for better validation
MONEY_RE = r"\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?"
PERCENTAGE_RE = r"\d+(?:\.\d+)?%"
DECIMAL_RE = r"\d+\.\d+"
WORD_STRONG_RE = r"[A-Za-z][A-Za-z\s\-]{2,50}[A-Za-z]"
NAME_RE = r"[A-Z][a-z]+\s[A-Z][a-z]+"
COMPANY_RE = r"[A-Z][a-zA-Z\s&\-\.,]{3,}"
ADDRESS_RE = r"\d+\s+[A-Za-z0-9\s\-\.,#]+"
ZIP_RE = r"\d{5}(?:-\d{4})?"
CREDIT_CARD_RE = r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}"
SSN_RE = r"\d{3}-\d{2}-\d{4}"
DRIVER_LICENSE_RE = r"[A-Z0-9]{8,15}"
PASSPORT_RE = r"[A-Z0-9]{6,9}"
IBAN_RE = r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}"

def _as_is(x): return x

def _phone_parse(raw: str) -> str:
    # normalize to E.164 if possible; otherwise return raw
    try:
        num = phonenumbers.parse(raw, None)
        if phonenumbers.is_possible_number(num) and phonenumbers.is_valid_number(num):
            return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    return raw

def register_defaults(reg: ParameterTypeRegistry) -> ParameterTypeRegistry:
    # Built-in parameter types (int, float, word, string) are already registered by the library
    # We only need to register custom parameter types

    # Now register custom parameter types
    reg.define_parameter_type(ParameterType(
        name="email", regexp=EMAIL_RE, type=str, transformer=_as_is, use_for_snippets=True, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="phone", regexp=r"[+()\-\s\d]{7,20}", type=str, transformer=_phone_parse, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="uuid", regexp=UUID_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="date_iso", regexp=DATE_ISO, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="time_iso", regexp=TIME_ISO, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="url", regexp=URL_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="aadhaar", regexp=AADHAAR, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="pan", regexp=PAN, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))

    # Enhanced parameter types for intelligent format validation
    reg.define_parameter_type(ParameterType(
        name="money", regexp=MONEY_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="percentage", regexp=PERCENTAGE_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="decimal", regexp=DECIMAL_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="name", regexp=NAME_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="company", regexp=COMPANY_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="address", regexp=ADDRESS_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="zip", regexp=ZIP_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="credit_card", regexp=CREDIT_CARD_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="ssn", regexp=SSN_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="driver_license", regexp=DRIVER_LICENSE_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="passport", regexp=PASSPORT_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))
    reg.define_parameter_type(ParameterType(
        name="iban", regexp=IBAN_RE, type=str, transformer=_as_is, use_for_snippets=False, prefer_for_regexp_match=False
    ))

    return reg
