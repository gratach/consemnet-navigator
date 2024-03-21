def getIndirectConnections(concept, RALFramework):
    """
    Get the indirect connections of a abstract concept.
    """
    connections = set()

    newConnections = RALFramework.searchRALJPattern([{"1" : [[concept, "2", 0], "+"]}])
    connections.update([(concept, newConnection["2"], newConnection["1"]) for newConnection in newConnections])
    newConnections = RALFramework.searchRALJPattern([{"1" : [[concept, 0, "2"], "+"]}])
    connections.update([(concept, newConnection["1"], newConnection["2"]) for newConnection in newConnections])
    newConnections = RALFramework.searchRALJPattern([{"1" : [[concept, 0, 0], "+"]}])
    connections.update([(concept, newConnection["1"], newConnection["1"]) for newConnection in newConnections])

    newConnections = RALFramework.searchRALJPattern([{"1" : [["2", concept, 0], "+"]}])
    connections.update([(newConnection["2"], concept, newConnection["1"]) for newConnection in newConnections])
    newConnections = RALFramework.searchRALJPattern([{"1" : [[0, concept, "2"], "+"]}])
    connections.update([(newConnection["1"], concept, newConnection["2"]) for newConnection in newConnections])
    newConnections = RALFramework.searchRALJPattern([{"1" : [[0, concept, 0], "+"]}])
    connections.update([(newConnection["1"], concept, newConnection["1"]) for newConnection in newConnections])

    newConnections = RALFramework.searchRALJPattern([{"1" : [["2", 0, concept], "+"]}])
    connections.update([(newConnection["2"], newConnection["1"], concept) for newConnection in newConnections])
    newConnections = RALFramework.searchRALJPattern([{"1" : [[0, "2", concept], "+"]}])
    connections.update([(newConnection["1"], newConnection["2"], concept) for newConnection in newConnections])
    newConnections = RALFramework.searchRALJPattern([{"1" : [[0, 0, concept], "+"]}])
    connections.update([(newConnection["1"], newConnection["1"], concept) for newConnection in newConnections])

    connections = set([(None if y == concept else y for y in x) for x in connections])
    return connections