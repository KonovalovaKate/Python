from langchain_core.tools import tool

# DOKA PRO size chart: (size_name, waist_min_cm, waist_max_cm) measured at rest
SIZE_CHART = [
    ("3XS", 50, 55),
    ("XXS", 50, 57),
    ("XS", 58, 63),
    ("S", 64, 68),
    ("M", 69, 74),
    ("L", 75, 81),
    ("XL", 82, 88),
    ("2XL", 89, 95),
    ("3XL", 96, 101),
    ("4XL", 102, 109),
    ("5XL", 110, 117),
    ("6XL", 118, 126),
]


def _find_size(waist_cm: float):
    # Returns the matching size row; clamps to smallest/largest if out of range
    for name, waist_min, waist_max in SIZE_CHART:
        if waist_min <= waist_cm <= waist_max:
            return name, waist_min, waist_max
    if waist_cm < SIZE_CHART[0][1]:
        return SIZE_CHART[0]
    return SIZE_CHART[-1]


def _shift_size(size_name: str, step: int):
    # Moves up (+) or down (-) the size chart by the given number of steps
    names = [row[0] for row in SIZE_CHART]
    index = names.index(size_name) + step
    if 0 <= index < len(names):
        return names[index]
    return None


@tool
def suggest_corset_size(
    waist_cm: float,
    goal: str = "waist_training",
    hip_cm: float = None,
    torso_length: str = "average",
) -> str:
    """Suggest a Dokasport corset size and model.
    Args: waist_cm - waist circumference in cm (measured at rest);
    goal - waist_training, weight_loss, postpartum, or spine_support;
    hip_cm - hip circumference in cm (optional);
    torso_length - short, average, or long (optional)."""
    size_name, waist_min, waist_max = _find_size(waist_cm)
    recommended_size = size_name
    notes = []

    # Recommend one size up when hips are 20+ cm wider than waist
    if hip_cm is not None and hip_cm >= waist_cm + 20:
        bigger = _shift_size(size_name, 1)
        if bigger:
            recommended_size = bigger
            notes.append(
                f"Стегна на 20+ см ширші за талію — рекомендовано розмір {bigger} замість {size_name}."
            )

    # For waist training, offer one size tighter with an extender as an option
    tighter_size = _shift_size(size_name, -1)
    if goal == "waist_training" and tighter_size:
        notes.append(
            f"Для тренування талії: стандарт {size_name}, або {tighter_size} з розширювачем "
            f"(жорсткіша утяжка, +5–7 см)."
        )

    # Select model based on torso length: 25 cm for short, 30 cm otherwise
    if torso_length == "short":
        model = "DOKA PRO 25"
        height = 25
        price = 1470
        url = "https://dokasport.com.ua/lateksnij-korset-dlya-shudnennya-na-25-metalevih-vstavok-25-u-visotu"
        alt_model = "DOKA PRO 30"
        alt_height = 30
        model_note = "Короткий торс — краще 25 см."
    else:
        model = "DOKA PRO 30"
        height = 30
        price = 1490
        url = "https://dokasport.com.ua/ortopedichniy-korset-na-25-metalevih-vstavok"
        alt_model = "DOKA PRO 25"
        alt_height = 25
        model_note = "Більше покриття та утяжка — 30 см."

    lines = [
        f"Талія {waist_cm} см → розмір {recommended_size} (діапазон {waist_min}–{waist_max} см).",
        f"Модель: {model}, висота {height} см, {price} грн. {model_note}",
        f"Посилання: {url}",
        f"Альтернатива: {alt_model} ({alt_height} см).",
        "Вимір: талія у найвужчому місці у втягнутому стані.",
    ]
    lines.extend(notes)
    return "\n".join(lines)
