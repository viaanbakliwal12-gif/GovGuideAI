from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from email_validator import EmailNotValidError, validate_email
import phonenumbers
import pycountry


class IdentifierValidationError(ValueError):
    """Raised when an email address or phone number is not structurally valid."""


@dataclass(frozen=True)
class CountryOption:
    code: str
    name: str
    dial_code: str
    flag: str


def normalize_email(value: str) -> str:
    try:
        result = validate_email(str(value or "").strip(), check_deliverability=False)
    except EmailNotValidError as error:
        raise IdentifierValidationError("Enter a valid email address.") from error

    # Account identifiers are case-insensitive in GovGuideAI. The validator also
    # normalizes Unicode domains safely before this comparison form is stored.
    return result.normalized.lower()


def normalize_phone_number(value: str, country_code: str | None = None) -> str:
    raw_value = str(value or "").strip()
    region = str(country_code or "").strip().upper() or None
    if not raw_value:
        raise IdentifierValidationError("Enter a valid phone number.")

    try:
        parsed = phonenumbers.parse(raw_value, None if raw_value.startswith("+") else region)
    except phonenumbers.NumberParseException as error:
        raise IdentifierValidationError("Enter a valid phone number.") from error

    if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(parsed):
        raise IdentifierValidationError("Enter a valid phone number.")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def mask_destination(destination: str, channel: str) -> str:
    if channel == "email":
        local, separator, domain = destination.partition("@")
        if not separator:
            return "***"
        shown = local[:1] if local else ""
        return f"{shown}***@{domain}"

    digits = destination.lstrip("+")
    if len(digits) <= 4:
        return f"+{'*' * len(digits)}"
    return f"+{digits[:2]}{'*' * max(4, len(digits) - 4)}{digits[-2:]}"


@lru_cache(maxsize=1)
def country_options() -> tuple[CountryOption, ...]:
    options: list[CountryOption] = []
    for region in phonenumbers.SUPPORTED_REGIONS:
        country = pycountry.countries.get(alpha_2=region)
        dial_code = phonenumbers.country_code_for_region(region)
        if country is None or not dial_code:
            continue
        options.append(
            CountryOption(
                code=region,
                name=country.name,
                dial_code=f"+{dial_code}",
                flag="".join(chr(127397 + ord(character)) for character in region),
            )
        )

    priority = {"IN": 0, "US": 1, "GB": 2}
    options.sort(key=lambda option: (priority.get(option.code, 3), option.name))
    return tuple(options)
