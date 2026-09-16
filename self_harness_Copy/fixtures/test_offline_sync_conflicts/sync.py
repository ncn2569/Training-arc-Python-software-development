def merge_notes(local, remote):
    """Return the currently preferred copy of each offline note."""
    result = dict(remote)
    result.update(local)
    return result
