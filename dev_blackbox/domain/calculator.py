def calculate_contribution_level(count: int, max_count: int) -> int:
    if count == 0 or max_count == 0:
        return 0

    ratio = count / max_count
    if ratio <= 0.25:
        return 1
    elif ratio <= 0.5:
        return 2
    elif ratio <= 0.75:
        return 3
    else:
        return 4
