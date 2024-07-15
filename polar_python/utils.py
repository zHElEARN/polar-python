def byte_to_bitmap(byte: int) -> list[bool]:
    binary_string = f"{byte:08b}"
    reversed_binary_string = binary_string[::-1]

    return [bit == '1' for bit in reversed_binary_string]