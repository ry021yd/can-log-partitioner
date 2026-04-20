import argparse
import glob
from pathlib import Path
import sys

from asc_split_checker import AscSplitChecker, load_rules_from_json
from file_splitter import FileSplitter, SplitEngine

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

def split_canasc(input_ascs, rule_json, output_dir):
    """Split CANASC files according to rules

    Args:
        input_ascs: list of input ASC files to process
        rule_json: JSON file containing rules for splitting
        output_dir: output directory to write results to

    Returns:
        results: list of results for each input file
    """

    output_dir = Path(output_dir)
    rules=load_rules_from_json(rule_json)

    for asc in input_ascs:
        if not asc.endswith(".asc"):
            print(f"Skipping non-ASC file: {asc}")
            continue
        output_dir.mkdir(parents=True, exist_ok=True)

        checker = AscSplitChecker(
            rules=rules
        )
        engine = SplitEngine(
            input_file=asc,
            output_dir=output_dir
        )
        splitter = FileSplitter(
            checker=checker,
            engine=engine
        )
        splitter.split_file(asc)

    return []

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_files", help="Input files to process; glob patterns are also accepted", nargs="+")
    parser.add_argument("rule_file", help="Rule file to use for judging to split or not")
    parser.add_argument("output_dir", help="Output directory to write results to")
    args = parser.parse_args()

    input_files = collect_files(args.input_files)
    split_canasc(
        input_ascs=input_files,
        rule_json=args.rule_file,
        output_dir=args.output_dir
    )

    return 0

if __name__ == "__main__":
    sys.exit(main())