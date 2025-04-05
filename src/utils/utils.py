from sqlalchemy.orm import class_mapper
from datetime import datetime


def parse_datetime_fields(data: dict, datetime_fields: list[str]) -> dict:
    for field in datetime_fields:
        if field in data and isinstance(data[field], str):
            try:
                data[field] = datetime.fromisoformat(data[field])
            except ValueError:
                pass
    return data


def to_dict(obj):
    result = {}
    for c in class_mapper(obj.__class__).columns:
        value = getattr(obj, c.key)
        if isinstance(value, datetime):
            result[c.key] = value.isoformat()
        else:
            result[c.key] = value
    return result
