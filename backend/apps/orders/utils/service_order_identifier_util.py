def generate_service_order_identifier(tenant_code: str, last_number: int) -> str:
    next_number = last_number + 1
    if last_number >= 9999:
        return f"{tenant_code}{next_number:05d}"
    return f"{tenant_code}{next_number:04d}"
