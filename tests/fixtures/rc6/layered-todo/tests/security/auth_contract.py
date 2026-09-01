from security.auth import authorize


def contract_witness() -> bool:
    return authorize("operator") is True
