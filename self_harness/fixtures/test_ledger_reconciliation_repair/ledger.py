"""Small cents-only ledger used by the repair benchmark."""


def reconcile(entries):
    balances = {}
    seen_ids = set()
    for entry in entries:
        entry_id = entry["id"]
        if entry_id in seen_ids:
            continue
        account = entry["account"]
        amount = entry["amount_cents"]
        balances[account] = balances.get(account, 0) + amount
    return {"balances": balances, "total_cents": sum(balances.values())}
