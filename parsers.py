import re
from datetime import datetime

CURRENCY_MAP = {"$": "USD", "USD": "USD", "EUR": "EUR"}

TEXT_FIELDS = [
    ("invoice_number", "NUMBER"),
    ("invoice_date", "DATE"),
    ("due_date", "DUE_DATE"),
    ("vendor_name", "SELLER_NAME"),
]
AMOUNT_FIELDS = [
    ("subtotal", "SUB_TOTAL"),
    ("tax", "TAX"),
    ("total", "TOTAL"),
]


def parse_amount(text):
    match = re.search(r"(\d[\d,]*\.?\d*)\s*(EUR|USD|\$)", text)
    if match is None:
        return None
    amount = float(match.group(1).replace(",", ""))
    currency = CURRENCY_MAP[match.group(2)]
    return amount, currency


def parse_number(text):
    pattern = r"^invoice\s*(id|#|number|no\.?)?\s*"
    cleaned = re.sub(pattern, "", text.strip(), flags=re.IGNORECASE)
    return cleaned or None


def parse_date(text):
    match = re.search(r"\d{1,2}-[A-Za-z]{3}-\d{4}", text)
    if match is None:
        return None
    parsed = datetime.strptime(match.group(), "%d-%b-%Y")
    return parsed.date().isoformat()


def parse_name(text):
    return text.strip() or None


TEXT_PARSERS = {
    "invoice_number": parse_number,
    "invoice_date": parse_date,
    "due_date": parse_date,
    "vendor_name": parse_name,
}


def get_text(data, key):
    value = data.get(key)
    if isinstance(value, dict):
        return value.get("text")
    return None


def build_record(data):
    record = {}
    problems = []
    currencies = []

    for field, key in TEXT_FIELDS:
        text = get_text(data, key)
        value = TEXT_PARSERS[field](text) if text else None
        if text and value is None:
            problems.append(key)
        record[field] = value

    for field, key in AMOUNT_FIELDS:
        text = get_text(data, key)
        parsed = parse_amount(text) if text else None
        if text and parsed is None:
            problems.append(key)
        record[field] = parsed[0] if parsed else None
        if parsed:
            currencies.append(parsed[1])

    if len(set(currencies)) > 1:
        problems.append("CURRENCY_MISMATCH")
    record["currency"] = currencies[0] if currencies else None
    return record, problems
