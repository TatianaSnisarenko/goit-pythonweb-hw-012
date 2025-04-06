from sqlalchemy.orm import class_mapper
from datetime import datetime
from typing import Any, List

"""
Utility functions module.

This module provides utility functions for working with SQLAlchemy models 
and handling datetime fields in dictionaries.

Functions:
    parse_datetime_fields: Parses and converts string datetime fields in a dictionary to `datetime` objects.
    to_dict: Converts a SQLAlchemy model instance to a dictionary.
"""


def parse_datetime_fields(data: dict, datetime_fields: List[str]) -> dict:
    """
    Parses and converts string datetime fields in a dictionary to `datetime` objects.

    Args:
        data (dict): The dictionary containing data to process.
        datetime_fields (List[str]): A list of keys in the dictionary that represent datetime fields.

    Returns:
        dict: The updated dictionary with datetime fields converted to `datetime` objects.
    """
    for field in datetime_fields:
        if field in data and isinstance(data[field], str):
            try:
                data[field] = datetime.fromisoformat(data[field])
            except ValueError:
                pass
    return data


def to_dict(obj: Any) -> dict:
    """
    Converts a SQLAlchemy model instance to a dictionary.

    Args:
        obj (Any): The SQLAlchemy model instance to convert.

    Returns:
        dict: A dictionary representation of the SQLAlchemy model instance.
    """
    result = {}
    for c in class_mapper(obj.__class__).columns:
        value = getattr(obj, c.key)
        if isinstance(value, datetime):
            result[c.key] = value.isoformat()
        else:
            result[c.key] = value
    return result
