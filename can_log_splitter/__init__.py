import glob
from pathlib import Path

from .asc_split_checker import AscSplitChecker, load_rules_from_json
from .file_splitter import FileSplitConfig, FileSplitter, SegmentMeta, SplitChecker, HeaderTarget, SegmentEvent

__all__ = [
    "split_canasc",
    "FileSplitConfig",
    "FileSplitter",
    "SplitChecker",
    "HeaderTarget",
    "SegmentEvent",
]

def collect_files(patterns: list[str]) -> list[str]:
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

def get_asc_header(input_asc, encoding="utf-8"):
    """Get ASC header lines for each segment file

    Args:
        input_asc: input ASC file path
        encoding: encoding of the files

    Returns:
        header_lines: tuple of header lines to prepend to each segment file
    """
    header_lines = []
    with Path(input_asc).open("r", encoding=encoding) as f:
        for line in f:
            parts = line.strip().split()
            if parts and parts[0].replace(".", "").isdigit():
                break
            header_lines.append(line)
    
    return tuple(header_lines)

def split_canasc(
        input_ascs: list[str],
        rule_json: str,
        output_dir: str,
        encoding="utf-8"
    ) -> list[SegmentMeta]:
    """Split CANASC files according to rules

    Args:
        input_ascs: list of input ASC files to process
        rule_json: JSON file containing rules for splitting
        output_dir: output directory to write results to
        encoding: encoding of the files

    Returns:
        results: list of results for each input file
    """

    output_dir = Path(output_dir)
    rules = load_rules_from_json(rule_json)
    results: list[SegmentMeta] = []

    for asc in input_ascs:
        if not asc.endswith(".asc"):
            print(f"Skipping non-ASC file: {asc}")
            continue
        output_dir.mkdir(parents=True, exist_ok=True)

        header_lines = get_asc_header(asc, encoding=encoding)

        checker = AscSplitChecker(
            rules=rules
        )
        config = FileSplitConfig(
            input_file=asc,
            output_dir=output_dir,
            header_lines=header_lines,
            encoding=encoding,
            initial_segment_name="initial"
        )
        splitter = FileSplitter(
            checker=checker,
            config=config
        )
        split_result = splitter.split_file()
        results.extend(split_result)

    return results