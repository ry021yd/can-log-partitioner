from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional

from file_splitter import SegmentEvent, SplitChecker

@dataclass
class AscMatchRule:
    segment_name: str
    condition_canid: Optional[str] = None
    condition_data: Optional[str] = None

    @staticmethod
    def _normalize_canid(value: str) -> str:
        return value.strip().upper()

    @staticmethod
    def _normalize_data(value: str) -> str:
        return value.replace(" ", "").replace("_", "").strip().upper()

    @staticmethod
    def parse_asc_frame(line: str) -> Optional[tuple[str, str]]:
        parts = line.strip().split()
        if not parts or len(parts) < 7:
            return None
        
        try:
            # Currently, CANXL frames are not supported
            if parts[1] == "CANFD":
                # CANFD
                canid = parts[4]
                byte_count = int(parts[8])
                data = "".join(parts[9:9 + byte_count])
            else:
                # Classic CAN
                canid = parts[2]
                byte_count = int(parts[5])
                data = "".join(parts[6:6 + byte_count])
            return canid, data
        except (IndexError):
            return None

    def matches(self, text: str) -> bool:
        parsed_frame = self.parse_asc_frame(text)
        if parsed_frame is None:
            return False
        canid, data = parsed_frame

        if self.condition_canid is None and self.condition_data is None:
            return False

        if self.condition_canid is not None:
            if self._normalize_canid(canid) != self._normalize_canid(self.condition_canid):
                return False
        
        if self.condition_data is not None:
            if self._normalize_data(data) != self._normalize_data(self.condition_data):
                return False
            
        return True

def load_rules_from_json(rule_file: Path) -> list[AscMatchRule]:
    with Path(rule_file).open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise ValueError("Rule file root must be an object.")
    rule_items = data.get("rules")
    if not isinstance(rule_items, list):
        raise ValueError("Rule file must contain a 'rules' array.")

    rules: list[AscMatchRule] = []
    for idx, item in enumerate(rule_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"rules[{idx}] must be an object.")

        rules.append(
            AscMatchRule(
                segment_name=str(item["segment_name"]),
                condition_canid=item.get("condition_canid"),
                condition_data=item.get("condition_data")
            )
        )
    return rules

class AscSplitChecker(SplitChecker):
    def __init__(
        self,
        rules: list[AscMatchRule],
    ) -> None:
        self.rules = rules
    def check_line(self, line: str) -> Optional[SegmentEvent]:
        for rule in self.rules:
            if rule.matches(line):
                return SegmentEvent.split_to(rule.segment_name)
        return None