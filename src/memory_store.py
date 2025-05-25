from cachetools import TTLCache
from uuid import uuid4
from typing import Any
from logger import log

_CACHE = TTLCache(maxsize=100, ttl=600)

def put_item(value: Any) -> str:
    """
    Store a value in the in-memory store and return a reference ID.

    Returns:
        str: A UUID reference key
    """
    
    ref_id = str(uuid4())
    _CACHE[ref_id] = value
    
    log.info(f"[memory_store] stored value under key '{ref_id}'")
    
    return ref_id

def get_item(ref_id: str) -> Any:
    """
    Retrieves a value by its reference key.

    Raises:
        Exception if the key is not found or has expired.
    """

    if ref_id not in _CACHE:
        log.error(f"[memory_store] key '{ref_id}' not found or expired.")
        raise Exception(f"Memory store key '{ref_id}' not found or expired.")
    
    return _CACHE[ref_id]

def delete_item(ref_id: str) -> None:
    """
    Delete an item from the store.

    Args:
        ref_id: The reference key to delete
    """
    
    if ref_id in _CACHE:
        _CACHE.pop(ref_id)
        log.info(f"[memory_store] deleted key '{ref_id}'")
