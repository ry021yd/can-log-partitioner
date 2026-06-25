from pathlib import Path

from can_bus_identifier.num2bus_map import Num2BusMap
from can_log_common.asc import get_asc_header

from .asc_route_resolver import AscRouteResolver
from .file_distributor import FileDistributeConfig, FileDistributor, RouteMeta


def distribute_canasc(
    input_ascs: list[str],
    num2bus_map_json: str,
    output_dir: str,
    encoding="utf-8",
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
            encoding=encoding,
        )
        distributor = FileDistributor(
            resolver=resolver,
            config=config,
        )
        distribute_result = distributor.distribute_file()
        results.extend(distribute_result)

    return results
