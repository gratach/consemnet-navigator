# Create abstract concepts of the reduced abstraction layer framework in the neo4j database.
# Documentation:
#   reduced abstraction layer framework : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/reduced-abstraction-layer-framework.md
#   constructed abstraction : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/constructed-abstraction.md
#   direct abstraction : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/direct-abstraction.md
#   data concept : https://github.com/gratach/thoughts/blob/master/topics/data/graph/data-concept.md

class neo4jRALFramework:
    def __init__(self, neo4j_session):
        self.neo4j_session = neo4j_session
    def ConstructedAbstraction(self, baseConnections):
        return ConstructedAbstraction(baseConnections, self.neo4j_session)
    def DirectDataAbstraction(self, datastring, formatstring):
        return DirectDataAbstraction(datastring, formatstring, self.neo4j_session)
    def DirectAbstraction(self, abstraction):
        return DirectAbstraction(abstraction, self.neo4j_session)
    def InverseDirectAbstraction(self, directAbstraction):
        return InverseDirectAbstraction(directAbstraction, self.neo4j_session)
    def deleteAbstraction(self, abstraction):
        deleteAbstraction(abstraction, self.neo4j_session)
    def getAbstractionType(self, abstraction):
        return getAbstractionType(abstraction, self.neo4j_session)
    def getAbstractionContent(self, abstraction):
        type = self.getAbstractionType(abstraction)
        if type == "DirectDataAbstraction":
            return getDirectDataAbstractionContent(abstraction, self.neo4j_session)
        elif type == "ConstructedAbstraction":
            return getBaseConnections(abstraction, self.neo4j_session)
        elif type == "DirectAbstraction":
            return getDirectAbstractionContent(abstraction, self.neo4j_session)
        elif type == "InverseDirectAbstraction":
            return getInverseDirectAbstractionContent(abstraction, self.neo4j_session)
        else:
            raise ValueError("The abstraction type is not valid.")
    def searchRALJPattern(self, pattern):
        return searchRALJPattern(pattern, self.neo4j_session)
    def listAllAbstractions(self):
        return listAllAbstractions(self.neo4j_session)

def ConstructedAbstraction(baseConnections, neo4j_session):
    """
    Creates an constructed abstraction in the neo4j database and returns the node id of the created constructed abstraction.
    """
    # Create the query string
    structureString = f"(n:ConstructedAbstraction:Abstraction {{connectionCount: {len(baseConnections)}}})"
    idDict = {}
    i = 0
    for connection in baseConnections:
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
    id = neo4j_session.run("MERGE (a:DirectDataAbstraction:Abstraction {data: $data, format: $format}) RETURN id(a)", data=datastring, format=formatstring).single().value()
    return id

def DirectAbstraction(abstraction, neo4j_session):
    """
    Creates the direct abstraction of an abstraction in the neo4j database and returns the node id of the created direct abstraction.
    """
    id = neo4j_session.run("MATCH (n) WHERE id(n) = $id MERGE (a:DirectAbstraction:Abstraction)-[:isAbstractionOf]->(n) RETURN id(a)", id=abstraction).single().value()
    return id

def InverseDirectAbstraction(directAbstraction, neo4j_session):
    """
    Creates the inverse direct abstraction of an abstraction in the neo4j database and returns the node id of the created direct abstraction.
    """
    id = neo4j_session.run("MATCH (n) WHERE id(n) = $id MERGE (a:InverseDirectAbstraction:Abstraction)-[:isInverseAbstractionOf]->(n) RETURN id(a)", id=directAbstraction).single().value()
    return id

def deleteAbstraction(id, neo4j_session):
    """
    Deletes the abstraction with the given id from the neo4j database.
    """
    # Check if there is a direct abstraction of the abstraction
    directAbstraction = neo4j_session.run("MATCH (n)-[:isAbstractionOf]->(m) WHERE id(m) = $id RETURN id(n)", id=id).single()
    if directAbstraction != None:
        raise ValueError("The abstraction can not be deleted because there is a DirectAbstraction that relies on it.")
    # Check if there is an inverse direct abstraction of the abstraction
    inverseDirectAbstraction = neo4j_session.run("MATCH (n)-[:isInverseAbstractionOf]->(m) WHERE id(m) = $id RETURN id(n)", id=id).single()
    if inverseDirectAbstraction != None:
        raise ValueError("The abstraction can not be deleted because there is an InverseDirectAbstraction that relies on it.")
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

def getBaseConnections(id, neo4j_session):
    """
    Returns the base connections of the abstraction with the given id.
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

def getInverseDirectAbstractionContent(id, neo4j_session):
    """
    Returns the id of the abstraction that the inverse direct abstraction with the given id is an inverse abstraction of.
    """
    abstraction = neo4j_session.run("MATCH (n)-[:isInverseAbstractionOf]->(m) WHERE id(n) = $id RETURN id(m)", id=id).single().value()
    return abstraction

def searchRALJPattern(pattern, neo4j_session):
    """
    Searches for appearances of the given pattern in the neo4j database and returns a list of dictionaries that map the ids of the ralj pattern to the neo4j ids of the appearances.
    The pattern can also contain neo4j ids which are maked by enclosing them in square brackets.
    When searching for constructed concepts that can have more than the listed connections, a "+" has to be added at the end of the connection list.
    When searching for direct data concepts with unknown data or format, the data or format can be set to 0.
    """
    assert type(pattern) == list and len(pattern) < 5
    constructedConceptBlock = pattern[0] if len(pattern) > 0 else {}
    dataConceptBlock = pattern[1] if len(pattern) > 1 else {}
    directAbstractionBlock = pattern[2] if len(pattern) > 2 else {}
    inverseDirectAbstractionBlock = pattern[3] if len(pattern) > 3 else {}
    structureStringArray = []
    globalIDs = set()
    localIDs = set()
    # Evaluate the dataConceptBlock
    for format, datalist in dataConceptBlock.items():
        for data, id in datalist.items():
            dataAndFormat = ", ".join([*([] if data == 0 else[f"data: '{data}'"]), *([] if format == 0 else[f"format: '{format}'"])])
            if type(id) == int:
                structureStringArray.append(f"(local{id}:DirectDataAbstraction {{{dataAndFormat}}})")
                localIDs.add(id)
            elif type(id) == list and len(id) == 1 and type(id[0]) == int:
                structureStringArray.append(f"(global{id[0]}:DirectDataAbstraction {{{dataAndFormat}}})")
                globalIDs.add(id[0])
            else:
                raise ValueError("The id of a data concept must be an int or a list with one int.")
    # Evaluate the constructedConceptBlock
    tripelIndex = 0
    for id, connections in constructedConceptBlock.items():
        if type(id) == int:
            idName = f"local{id}"
            localIDs.add(id)
        elif type(id) == list and len(id) == 1 and type(id[0]) == int:
            idName = f"global{id[0]}"
            globalIDs.add(id[0])
        else:
            raise ValueError("The id of a constructed concept must be an int or a list with one int.")
        if len(connections) > 0 and list(connections)[-1] == "+":
            connections = list(connections)[:-1]
            structureStringArray.append(f"({idName}:ConstructedAbstraction)")
        else:
            structureStringArray.append(f"({idName}:ConstructedAbstraction {{connectionCount: {len(connections)}}})")
        for connection in connections:
            structureStringArray.append(f"({idName})-[:ownsTriple]->(triple{tripelIndex}:AbstractionTriple)")
            for i, triple in enumerate(connection):
                if type(triple) == int:
                    if triple == 0:
                        structureStringArray.append(f"(triple{tripelIndex})-[:{['subj', 'pred', 'obj'][i]}]->({idName})")
                    else:
                        structureStringArray.append(f"(triple{tripelIndex})-[:{['subj', 'pred', 'obj'][i]}]->(local{triple})")
                        localIDs.add(triple)
                elif type(triple) == list and len(triple) == 1 and type(triple[0]) == int:
                    structureStringArray.append(f"(triple{tripelIndex})-[:{['subj', 'pred', 'obj'][i]}]->(global{triple[0]})")
                    globalIDs.add(triple[0])
                else:
                    raise ValueError("The id of a triple concept must be an int or a list with one int.")
            tripelIndex += 1
    # Evaluate the directAbstractionBlock
    for id, abstraction in directAbstractionBlock.items():
        if type(id) == int:
            idName = f"local{id}"
            localIDs.add(id)
        elif type(id) == list and len(id) == 1 and type(id[0]) == int:
            idName = f"global{id[0]}"
            globalIDs.add(id[0])
        else:
            raise ValueError("The id of a direct abstraction must be an int or a list with one int.")
        if type(abstraction) == int:
            structureStringArray.append(f"({idName}:DirectAbstraction)-[:isAbstractionOf]->(local{abstraction})")
            localIDs.add(abstraction)
        elif type(abstraction) == list and len(abstraction) == 1 and type(abstraction[0]) == int:
            structureStringArray.append(f"({idName}:DirectAbstraction)-[:isAbstractionOf]->(global{abstraction[0]})")
            globalIDs.add(abstraction[0])
        else:
            raise ValueError("The id of an abstraction must be an int or a list with one int.")
    # Evaluate the inverseDirectAbstractionBlock
    for id, abstraction in inverseDirectAbstractionBlock.items():
        if type(id) == int:
            idName = f"local{id}"
            localIDs.add(id)
        elif type(id) == list and len(id) == 1 and type(id[0]) == int:
            idName = f"global{id[0]}"
            globalIDs.add(id[0])
        else:
            raise ValueError("The id of an inverse direct abstraction must be an int or a list with one int.")
        if type(abstraction) == int:
            structureStringArray.append(f"({idName}:InverseDirectAbstraction)-[:isInverseAbstractionOf]->(local{abstraction})")
            localIDs.add(abstraction)
        elif type(abstraction) == list and len(abstraction) == 1 and type(abstraction[0]) == int:
            structureStringArray.append(f"({idName}:InverseDirectAbstraction)-[:isInverseAbstractionOf]->(global{abstraction[0]})")
            globalIDs.add(abstraction[0])
        else:
            raise ValueError("The id of an abstraction must be an int or a list with one int.")
    # Create the query string
    structureString = "MATCH " + ", ".join(structureStringArray)
    if len(globalIDs) > 0:
        structureString += " WHERE " +  " AND ".join([f"id(global{id}) = {id}" for id in globalIDs])
    if len(localIDs) == 0:
        raise ValueError("The pattern must contain at least one local id.")
    localIDs = list(localIDs)
    structureString += " RETURN " + ", ".join([f"id(local{id})" for id in localIDs])
    # Execute the query and return the result as a list of dictionaries
    result = neo4j_session.run(structureString).values()
    result = [dict(zip(localIDs, record)) for record in result]
    return result

def listAllAbstractions(neo4j_session):
    """
    Returns a list of all abstractions in the neo4j database.
    """
    result = neo4j_session.run("MATCH (n:Abstraction) RETURN id(n)").value()
    return result