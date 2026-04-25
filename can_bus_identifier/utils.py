import glob

def hex_canid_to_int(value: str) -> int:
    value = value.strip()
    return int(value, 16)

def int_canid_to_hex(value: int) -> str:
    return f"0x{value:X}"

def collect_files(patterns):
    """Collect files by glob patterns
    Args:
        patterns: array of glob patterns

    Returns:
        files: list of matching files
    """
    files = []
    for p in patterns:
        matches = sorted(glob.glob(p))
        if matches:
            files.extend(matches)
        else:
            files.append(p)
    return files