def mask(value: str, visible_length: int = 4) -> str:
    if len(value) <= visible_length:
        return "*" * len(value)
    return value[:visible_length] + "*" * (len(value) - visible_length)
