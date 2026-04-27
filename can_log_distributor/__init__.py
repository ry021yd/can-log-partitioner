import glob
from pathlib import Path

from can_bus_identifier.num2bus_map import Num2BusMap
from can_log_distributor.asc_route_resolver import AscRouteResolver
from can_log_distributor.file_distributor import FileDistributeConfig, FileDistributor, RouteMeta

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

def distribute_canasc(
        input_ascs: list[str],
        num2bus_map_json: str,
        output_dir: str,
        encoding="utf-8"
    ) -> list[RouteMeta]:

    output_dir = Path(output_dir)
    num2bus_map = Num2BusMap.load_json(num2bus_map_json)
    results: list[RouteMeta] = []

    for asc in input_ascs:
        if not asc.endswith(".asc"):
            print(f"Skipping non-ASC file: {asc}")
            continue
        output_dir.mkdir(parents=True, exist_ok=True)

        header_lines = get_asc_header(asc, encoding=encoding)

        resolver = AscRouteResolver(
            num2bus_map=num2bus_map
        )
        config = FileDistributeConfig(
            input_file=asc,
            output_dir=output_dir,
            header_lines=header_lines,
            encoding=encoding
        )
        distributor = FileDistributor(
            resolver=resolver,
            config=config
        )
        distribute_result = distributor.distribute_file()
        results.extend(distribute_result)

    return results