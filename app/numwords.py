"""Amount in words, Indian system (thousand, lakh, crore) - printed on payslips like a real one."""

_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
         "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _below_hundred(n):
    return _ONES[n] if n < 20 else (_TENS[n // 10] + (" " + _ONES[n % 10] if n % 10 else ""))


def _below_thousand(n):
    parts = []
    if n >= 100:
        parts.append(_ONES[n // 100] + " Hundred")
        n %= 100
    if n:
        parts.append(_below_hundred(n))
    return " ".join(parts)


def _whole_in_words(n):
    if n == 0:
        return "Zero"
    parts = []
    for unit, size in (("Crore", 10_000_000), ("Lakh", 100_000), ("Thousand", 1_000)):
        if n >= size:
            parts.append(_below_hundred(n // size) if size > 1_000 or n // size < 100 else _below_thousand(n // size))
            parts[-1] += " " + unit
            n %= size
    if n:
        parts.append(_below_thousand(n))
    return " ".join(parts)


def rupees_in_words(value):
    """90623.5 -> 'Rupees Ninety Thousand Six Hundred Twenty Three and Fifty Paise Only'"""
    try:
        paise_total = round(abs(float(value)) * 100)
    except (TypeError, ValueError):
        return ""
    rupees, paise = divmod(paise_total, 100)
    text = "Rupees " + _whole_in_words(rupees)
    if paise:
        text += " and " + _below_hundred(paise) + " Paise"
    return text + " Only"
