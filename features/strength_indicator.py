# features/strength_indicator.py
def check_password_strength_util(password: str, translator):
    """
    Calculates password strength and returns text and color.
    Returns: (strength_text: str, style_sheet_color: str)
    """
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)
    score = 0

    if length == 0: # Handle empty password case specifically
        return translator.tr("password_strength_very_weak"), "color: grey;"


    if length >= 8: score += 1
    if length >= 12: score += 1
    if has_upper and has_lower: score += 1
    if has_digit: score += 1
    if has_symbol: score += 1

    if score >= 4: # 4 or 5
        return translator.tr("password_strength_strong"), "color: green;"
    elif score == 3:
        return translator.tr("password_strength_medium"), "color: orange;"
    elif score == 2:
        return translator.tr("password_strength_weak"), "color: red;"
    else: # 0 or 1 (and not empty)
        return translator.tr("password_strength_very_weak"), "color: darkred;"