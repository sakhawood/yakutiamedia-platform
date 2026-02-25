def normalize_phone(raw_phone: str) -> str:
    digits = "".join(filter(str.isdigit, raw_phone))

    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]

    if digits.startswith("7") and len(digits) == 11:
        return "+7" + digits[1:]

    if digits.startswith("9") and len(digits) == 10:
        return "+7" + digits

    return None