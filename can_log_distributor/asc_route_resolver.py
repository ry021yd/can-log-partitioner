from typing import Optional

from can_bus_identifier.asc_frame import parse_asc_frame
from can_bus_identifier.num2bus_map import Num2BusMap
from .file_distributor import RouteEvent, RouteResolver, RouteSpec

class AscRouteResolver(RouteResolver):
    def __init__(
        self,
        num2bus_map: Num2BusMap
    ):
        self.num2bus_map = num2bus_map
    
    def check_line(self, line: str) -> Optional[RouteEvent]:
        frame = parse_asc_frame(line)
        if not frame:
            return None
        label = self.num2bus_map.get_label(frame.bus_number)
        if label is None:
            raise ValueError(f"Unknown bus number in ASC: {frame.bus_number}")
        return RouteEvent.route_to(label)