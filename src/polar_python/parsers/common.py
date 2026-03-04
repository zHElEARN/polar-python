"""Common utility functions for parsing operations."""

from typing import List


def byte_to_bitmap(byte: int) -> List[bool]:
    """Convert a byte to a bitmap (list of booleans)."""
    binary_string = f"{byte:08b}"
    reversed_binary_string = binary_string[::-1]
    return [bit == "1" for bit in reversed_binary_string]
