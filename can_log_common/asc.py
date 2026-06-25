from pathlib import Path


def get_asc_header(input_asc: str | Path, encoding: str = "utf-8") -> tuple[str, ...]:
    """Get ASC header lines before the first data-like row."""
    header_lines = []
    with Path(input_asc).open("r", encoding=encoding) as fp:
        for line in fp:
            parts = line.strip().split()
            if parts and parts[0].replace(".", "").isdigit():
                break
            header_lines.append(line)

    return tuple(header_lines)
