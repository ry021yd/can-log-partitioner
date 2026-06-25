import glob


def collect_files(patterns: list[str]) -> list[str]:
    """Collect files by glob patterns."""
    files = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            files.extend(matches)
        else:
            files.append(pattern)
    return files
