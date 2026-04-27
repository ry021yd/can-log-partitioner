from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any


@dataclass(frozen=True)
class Num2BusMap:
    bus_number_to_label: dict[str, str] = field(default_factory=dict)

    def get_label(self, bus_number: str) -> str | None:
        return self.bus_number_to_label.get(bus_number)

    @classmethod
    def from_json_dict(
        cls,
        data: list[dict[str, Any]],
        *,
        allow_unresolved: bool = False,
    ) -> "Num2BusMap":
        result: dict[str, str] = {}

        for idx, item in enumerate(data, start=1):
            bus_number = item.get("bus_number")
            status = item.get("result")
            labels = item.get("labels")

            if not isinstance(bus_number, str):
                raise ValueError(f"[{idx}].bus_number must be a string.")
            if not isinstance(status, str):
                raise ValueError(f"[{idx}].result must be a string.")
            if not isinstance(labels, list) or not all(isinstance(x, str) for x in labels):
                raise ValueError(f"[{idx}].labels must be a list[str].")

            if status != "resolved":
                if allow_unresolved:
                    continue
                raise ValueError(f"Bus {bus_number} is not resolved: {status}")

            if len(labels) != 1:
                if allow_unresolved:
                    continue
                raise ValueError(f"Bus {bus_number} must have exactly one label.")

            result[bus_number] = labels[0]

        return cls(result)

    @classmethod
    def load_json(
        cls,
        json_file: str | Path,
        *,
        allow_unresolved: bool = False,
    ) -> "Num2BusMap":
        with Path(json_file).open("r", encoding="utf-8") as fp:
            return cls.from_json_dict(
                json.load(fp),
                allow_unresolved=allow_unresolved,
            )