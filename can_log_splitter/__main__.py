import argparse
import sys

from . import collect_files, split_canasc

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_files", help="Input files to process; glob patterns are also accepted", nargs="+")
    parser.add_argument("rule_file", help="Rule file to use for judging to split or not")
    parser.add_argument("output_dir", help="Output directory to write results to")
    parser.add_argument("--encoding", help="Encoding of the files (default: utf-8)", default="utf-8")
    args = parser.parse_args()

    input_files = collect_files(args.input_files)
    split_canasc(
        input_ascs=input_files,
        rule_json=args.rule_file,
        output_dir=args.output_dir,
        encoding=args.encoding,
    )

    return 0

if __name__ == "__main__":
    sys.exit(main())