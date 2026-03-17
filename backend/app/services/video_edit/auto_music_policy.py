def choose_music(category_name: str) -> str:
    """
    Automatically select background music based on category.
    """

    if not category_name:
        return "happy_rhythm"

    c = category_name.lower()

    if "horror" in c or "scary" in c:
        return "breathing_shadows"

    if "motivation" in c or "inspiration" in c:
        return "brilliant_symphony"

    if "asmr" in c or "relax" in c:
        return "peaceful_vibes"

    if "story" in c:
        return "quiet_before_storm"

    if "facts" in c or "education" in c:
        return "happy_rhythm"

    return "happy_rhythm"