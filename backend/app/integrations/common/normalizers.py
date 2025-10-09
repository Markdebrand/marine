"""Helpers genéricos de normalización compartidos."""

def to_str(value):
    if value in (None, False, ""):
        return ""
    return str(value)


def to_bool(value):
    if value in (None, "", False):
        return False
    if value is True:
        return True
    try:
        if isinstance(value, (int, float)):
            return int(value) != 0
    except Exception:
        pass
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "yes", "y", "t", "on"):
            return True
        if v in ("0", "false", "no", "n", "f", "off"):
            return False
        try:
            return int(v) != 0
        except Exception:
            return True
    return bool(value)


def to_m2o(value):
    if not value or value in (False, None, "", []):
        return None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            _id = int(value[0]) if value[0] is not None else None
        except Exception:
            _id = None
        _name = to_str(value[1])
        return [_id, _name]
    return [None, to_str(value)]


def to_m2m_ids(value):
    if not value or value in (False, None, ""):
        return []
    if isinstance(value, (list, tuple)):
        out = []
        for v in value:
            try:
                out.append(int(v))
            except Exception:
                continue
        return out
    try:
        return [int(value)]
    except Exception:
        return []
