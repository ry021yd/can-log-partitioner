import sys
import argparse
import json
import pprint

from id2bus_map import Id2BusMap

def main():
    # get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-L", "--label-map", help="JSON file containing file pattern to bus label mapping")
    parser.add_argument("-O", "--output", help="output file")
    parser.add_argument("files", nargs="*", help="DBC files for parse, JSON files for input; glob patterns are also accepted")
    args = parser.parse_args()

    if not args.files:
        parser.print_help()
        return 1
    
    id2bus = Id2BusMap.from_dbc_with_label_map_json(args.files, args.label_map).to_json_dict()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            json.dump(id2bus, fp, ensure_ascii=False, indent=2)
    else:
        pprint.pprint(id2bus)

    return 0

if __name__ == '__main__':
    sys.exit(main())

