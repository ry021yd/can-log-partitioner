from pathlib import Path

from can_log_common.asc import get_asc_header

from .asc_split_checker import AscSplitChecker, load_rules_from_json
from .file_splitter import FileSplitConfig, FileSplitter, SegmentMeta


def split_canasc(
    input_ascs: list[str],
    rule_json: str,
    output_dir: str,
    encoding="utf-8",
) -> list[SegmentMeta]:
    """Split CANASC files according to rules."""
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
            initial_segment_name="initial",
        )
        splitter = FileSplitter(
            checker=checker,
            config=config,
        )
        split_result = splitter.split_file()
        results.extend(split_result)

    return results
