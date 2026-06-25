from can_log_common.files import collect_files

def hex_canid_to_int(value: str) -> int:
    value = value.strip()
    if value.endswith(('x', 'X')):
        value = value[:-1]
    return int(value, 16)

def int_canid_to_hex(value: int) -> str:
    return f"0x{value:X}"
