import uuid


def create_job(*, extracted: dict) -> str:
    # Mock downstream job creation for Day 2.
    # In Day 3 this would be replaced with a real integration.
    return str(uuid.uuid4())
