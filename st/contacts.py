import os
from typing import List
from langchain.agents import tool

CONTACTS = [{"name": "Test Venue", "phone":os.environ.get('TEST_PHONE_NUMBER')}]


@tool("get_all_contacts")
def get_all_contacts(placeholder: str) -> List[dict]:
    """Get contacts."""
    return CONTACTS
