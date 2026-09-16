def release_order(graph):
    remaining = {name: set(deps) for name, deps in graph.items()}
    order = []
    while remaining:
        ready = sorted(name for name, deps in remaining.items() if not deps)
        if not ready:
            return order
        for name in ready:
            order.append(name)
            remaining.pop(name)
        for deps in remaining.values():
            deps.difference_update(ready)
    return order
