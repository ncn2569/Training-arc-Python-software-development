def can_book(existing, provider, start, end):
    if end < start:
        raise ValueError("end must follow start")
    for appointment in existing:
        if not (end < appointment["start"] or start > appointment["end"]):
            return False
    return True
