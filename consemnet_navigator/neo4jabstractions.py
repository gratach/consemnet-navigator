# Create abstract concepts of the reduced abstraction layer framework in the neo4j database.
# Documentation:
#   reduced abstraction layer framework : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/reduced-abstraction-layer-framework.md
#   constructed abstraction : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/constructed-abstraction.md
#   direct abstraction : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/direct-abstraction.md
#   data concept : https://github.com/gratach/thoughts/blob/master/topics/data/graph/data-concept.md


def ConstructedAbstraction(semanticConnections, neo4j_session):
    """
    Creates an constructed abstraction in the neo4j database and returns the node id of the created constructed abstraction.
    """
    # Create the query string
    structureString = f"(n:ConstructedAbstraction {{connectionCount: {len(semanticConnections)}}})"
    idDict = {}
    i = 0
    for connection in semanticConnections:
        subj, pred, obj = connection
        if not None in connection:
            raise ValueError("The semantic connection must contain at least one None value.")
        if subj == None:
            subj = "(n)"
        else:
            assert type(subj) == int
            idDict[f"c{i}"] = subj
            subj = f"(c{i})"
            i += 1
        if pred == None:
            pred = "(n)"
        else:
            assert type(pred) == int
            idDict[f"c{i}"] = pred
            pred = f"(c{i})"
            i += 1
        if obj == None:
            obj = "(n)"
        else:
            assert type(obj) == int
            idDict[f"c{i}"] = obj
            obj = f"(c{i})"
            i += 1
        structureString += f", (n)-[:ownsTriple]->(c{i}:AbstractionTriple)-[:subj]->{subj}, (c{i})-[:pred]->{pred}, (c{i})-[:obj]->{obj}"
        i += 1
    idCompareString = ""
    if len(idDict) > 0:
        idCompareString += " WHERE "
        for name, id in idDict.items():
            idCompareString += f"id({name}) = {id} AND "
        idCompareString = idCompareString[:-5]
    matchString = f"MATCH {structureString} {idCompareString} RETURN id(n)"
    createString = ""
    if len(idDict) > 0:
        createString = "MATCH " + ", ".join([f"({k})" for k in idDict.keys()])
    createString += f"{idCompareString} CREATE {structureString} RETURN id(n)"
    # Test if the constructed abstraction already exists
    id = neo4j_session.run(matchString).single()
    if id == None:
        # Create the constructed abstraction
        id = neo4j_session.run(createString).single().value()
    else:
        id = id.value()
    return id

def DirectDataAbstraction(datastring, formatstring, neo4j_session):
    """
    Creates the direct abstraction of a data concept in the neo4j database and returns the node id of the created direct abstraction.
    """
    id = neo4j_session.run("MERGE (a:DirectDataAbstraction {data: $data, format: $format}) RETURN id(a)", data=datastring, format=formatstring).single().value()
    return id

def DirectAbstraction(abstraction, neo4j_session):
    """
    Creates the direct abstraction of an abstraction in the neo4j database and returns the node id of the created direct abstraction.
    """
    id = neo4j_session.run("MATCH (n) WHERE id(n) = $id MERGE (a:DirectAbstraction)-[:isAbstractionOf]->(n) RETURN id(a)", id=abstraction).single().value()
    return id

def deleteAbstraction(id, neo4j_session):
    """
    Deletes the abstraction with the given id from the neo4j database.
    """
    # Check if there is a direct abstraction of the abstraction
    directAbstraction = neo4j_session.run("MATCH (n)-[:isAbstractionOf]->(m) WHERE id(m) = $id RETURN id(n)", id=id).single()
    if directAbstraction != None:
        raise ValueError("The abstraction can not be deleted because there is a DirectAbstraction that relies on it.")
    # Get all the ids of the connected AbstractionTriples
    connectedTriples = set()
    for conn in ["subj", "pred", "obj"]:
        result = neo4j_session.run(f"MATCH (t:AbstractionTriple)-[:{conn}]->(n) WHERE id(n) = $id RETURN id(t)", id=id).value()
        for record in result:
            connectedTriples.add(record)
    # Check if all of the connected AbstractionTriples are owned by the removed abstraction
    ownedTriples = set(neo4j_session.run("MATCH (n)-[:ownsTriple]->(m) WHERE id(n) = $id RETURN id(m)", id=id).value())
    if connectedTriples != ownedTriples:
        raise ValueError("The abstraction can not be deleted because there are ConstructedAbstractions that rely on it.")
    # Delete the owned AbstractionTriples
    for triple in ownedTriples:
        neo4j_session.run("MATCH (n) WHERE id(n) = $id DETACH DELETE n", id=triple)
    # Delete the abstraction
    neo4j_session.run("MATCH (n) WHERE id(n) = $id DETACH DELETE n", id=id)

def getSemanticConnections(id, neo4j_session):
    """
    Returns the semantic connections of the abstraction with the given id.
    """
    ownedTriples = set(neo4j_session.run("MATCH (n)-[:ownsTriple]->(m) WHERE id(n) = $id RETURN id(m)", id=id).value())
    semanticConnections = []
    for triple in ownedTriples:
        subj = neo4j_session.run("MATCH (t)-[:subj]->(n) WHERE id(t) = $id RETURN id(n)", id=triple).single().value()
        pred = neo4j_session.run("MATCH (t)-[:pred]->(n) WHERE id(t) = $id RETURN id(n)", id=triple).single().value()
        obj = neo4j_session.run("MATCH (t)-[:obj]->(n) WHERE id(t) = $id RETURN id(n)", id=triple).single().value()
        semanticConnections.append((None if subj ==  id else subj, None if pred == id else pred, None if obj == id else obj))
    return frozenset(semanticConnections)

def getAbstractionType(id, neo4j_session):
    """
    Returns the type of the abstraction with the given id.
    """
    type = neo4j_session.run("MATCH (n) WHERE id(n) = $id RETURN labels(n)", id=id).single().value()
    return type[0]

def getDirectDataAbstractionContent(id, neo4j_session):
    """
    Returns the data and format of the direct abstraction with the given id.
    """
    data = neo4j_session.run("MATCH (n:DirectDataAbstraction) WHERE id(n) = $id RETURN n.data", id=id).single().value()
    format = neo4j_session.run("MATCH (n:DirectDataAbstraction) WHERE id(n) = $id RETURN n.format", id=id).single().value()
    return (data, format)

def getDirectAbstractionContent(id, neo4j_session):
    """
    Returns the id of the abstraction that the direct abstraction with the given id is an abstraction of.
    """
    abstraction = neo4j_session.run("MATCH (n)-[:isAbstractionOf]->(m) WHERE id(n) = $id RETURN id(m)", id=id).single().value()
    return abstraction