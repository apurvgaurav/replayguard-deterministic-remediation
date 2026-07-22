import pytest
from app.main import ledger_service

@pytest.fixture(autouse=True)
def use_temp_ledger(tmp_path):
    """
    Automatically redirect the global ledger_service to write to a temp file
    for the duration of every test.
    """
    original_path = ledger_service.ledger_path
    temp_ledger = tmp_path / "ledger_history_test.json"
    ledger_service.ledger_path = temp_ledger
    # Initialize the temp ledger file
    ledger_service._ensure_ledger_file()

    try:
        yield temp_ledger
    finally:
        # Restore original ledger path
        ledger_service.ledger_path = original_path
