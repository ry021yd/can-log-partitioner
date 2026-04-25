from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
import json

@dataclass(frozen=True)
class BusLabelRule:
    file_pattern: str
    bus_label: str

@dataclass
class BusLabelMap:
    rules: list[BusLabelRule] = field(default_factory=list)

    def resolve(self, file: str) -> str:
        name = Path(file).name
        for rule in self.rules:
            if fnmatch(name, rule["file_pattern"]):
                return rule.bus_label
        return Path(file).stem

    @classmethod
    def load_json(cls, json_file: str) -> "BusLabelMap":
        with open(json_file, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            items = data.get("map")
            if not isinstance(items, list):
                raise ValueError("Invalid JSON format: 'map' should be a list")

        rules: list[BusLabelRule] = []
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"map[{idx}] should be a dict")

            file_pattern = item.get("file_pattern")
            bus_label = item.get("bus_label")

            if not isinstance(file_pattern, str) or not file_pattern:
                raise ValueError(f"map[{idx}].file_pattern should be a non-empty string")
            if not isinstance(bus_label, str) or not bus_label:
                raise ValueError(f"map[{idx}].bus_label should be a non-empty string")

            rules.append(BusLabelRule(file_pattern, bus_label))
        return cls(rules)