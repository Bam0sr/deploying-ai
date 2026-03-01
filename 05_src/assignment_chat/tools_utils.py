"""Service 3: kitchen utility tools."""

from langchain.tools import tool

# Found this online, hope that's cool
CONVERSION_TABLE = {
    ("cups", "ml"): 236.588,
    ("cups", "liters"): 0.236588,
    ("ml", "cups"): 1 / 236.588,
    ("ml", "liters"): 0.001,
    ("liters", "ml"): 1000,
    ("liters", "cups"): 1 / 0.236588,
    ("oz", "grams"): 28.3495,
    ("oz", "kg"): 0.0283495,
    ("grams", "oz"): 1 / 28.3495,
    ("grams", "kg"): 0.001,
    ("kg", "grams"): 1000,
    ("kg", "oz"): 1 / 0.0283495,
    ("tablespoons", "ml"): 14.787,
    ("ml", "tablespoons"): 1 / 14.787,
    ("teaspoons", "ml"): 4.929,
    ("ml", "teaspoons"): 1 / 4.929,
    ("tablespoons", "teaspoons"): 3,
    ("teaspoons", "tablespoons"): 1 / 3,
    ("fahrenheit", "celsius"): None,  # handled specially
    ("celsius", "fahrenheit"): None,
    ("lbs", "kg"): 0.453592,
    ("kg", "lbs"): 1 / 0.453592,
    ("lbs", "grams"): 453.592,
    ("grams", "lbs"): 1 / 453.592,
}


@tool
def convert_cooking_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert common cooking units."""
    from_key = from_unit.lower().strip()
    to_key = to_unit.lower().strip()

    if from_key == to_key:
        return f"{value} {from_unit} is already in {to_unit}."

    if from_key == "fahrenheit" and to_key == "celsius":
        result = (value - 32) * 5 / 9
        return f"{value}°F = {result:.1f}°C"
    if from_key == "celsius" and to_key == "fahrenheit":
        result = value * 9 / 5 + 32
        return f"{value}°C = {result:.1f}°F"

    factor = CONVERSION_TABLE.get((from_key, to_key))
    if factor is None:
        return (
            f"Sorry, I don't know how to convert from {from_unit} to {to_unit}. "
            f"Supported units: cups, ml, liters, oz, grams, kg, lbs, "
            f"tablespoons, teaspoons, fahrenheit, celsius."
        )

    result = value * factor
    return f"{value} {from_unit} = {result:.4g} {to_unit}"


@tool
def adjust_servings(
    original_servings: int,
    target_servings: int,
    ingredients: str,
) -> str:
    """Scale ingredient amounts for a new serving count."""
    if original_servings <= 0:
        return "Original servings must be a positive number."

    ratio = target_servings / original_servings
    lines = ingredients.strip().split("\n")
    scaled = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        try:
            qty = float(parts[0])
            rest = parts[1] if len(parts) > 1 else ""
            new_qty = qty * ratio
            if new_qty == int(new_qty):
                scaled.append(f"{int(new_qty)} {rest}".strip())
            else:
                scaled.append(f"{new_qty:.2f} {rest}".strip())
        except (ValueError, IndexError):
            scaled.append(line)

    return (
        f"Scaled from {original_servings} to {target_servings} servings "
        f"(×{ratio:.2f}):\n" + "\n".join(scaled)
    )
