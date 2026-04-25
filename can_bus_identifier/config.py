from dataclasses import dataclass, field
import json
from pathlib import Path

from utils import hex_canid_to_int

@dataclass(frozen=True)
class IgnoreIdRule:
    value: int
    mask: int

    def matches(self, can_id: int) -> bool:
        return (can_id & self.mask) == (self.value & self.mask)

@dataclass(frozen=True)
class IdentifierConfig:
    ignore_ids: set[int] = field(default_factory=set)
    ignore_id_rules: list[IgnoreIdRule] = field(default_factory=list)

    def match_ignore_rules(self, can_id: int) -> bool:
        if can_id in self.ignore_ids:
            return True

        return any(rule.matches(can_id) for rule in self.ignore_id_rules)

def load_config_json(json_file: str | Path | None) -> IdentifierConfig:
    if not json_file:
        return IdentifierConfig()
    with Path(json_file).open("r", encoding="utf-8") as fp:
        data = json.load(fp)
        ids = data.get("ignore_ids")
        rules = data.get("ignore_id_rules")

        if ids is None:
            return_ids: set[int] = set()
        elif not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            raise ValueError(f"'ignore_ids' must be a list[str].")
        else:
            return_ids = {hex_canid_to_int(id) for id in ids}

        if rules is None:
            return_rules: list[IgnoreIdRule] = []
        else:
            if not isinstance(rules, list):
                raise ValueError("'ignore_id_rules' must be a list.")

            return_rules: list[IgnoreIdRule] = []
            for idx, rule in enumerate(rules, start=1):
                if not isinstance(rule, dict):
                    raise ValueError(f"ignore_id_rules[{idx}] must be a dict.")

                value = rule.get("value")
                mask = rule.get("mask")
                if not isinstance(value, str):
                    raise ValueError(f"ignore_id_rules[{idx}].value must be a string.")
                if not isinstance(mask, str):
                    raise ValueError(f"ignore_id_rules[{idx}].mask must be a string.")

                return_rules.append(
                    IgnoreIdRule(hex_canid_to_int(value), hex_canid_to_int(mask))
                )
        
    return IdentifierConfig(return_ids, return_rules)