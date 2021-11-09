def quote_arg(s: str) -> str:
    """Return a quoted cmd arg, with all backslashes and double quotes escaped"""
    escaped = s.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'
