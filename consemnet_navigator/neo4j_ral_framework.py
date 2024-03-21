# Create abstract concepts of the reduced abstraction layer framework in the neo4j database.
# Documentation:
#   reduced abstraction layer framework : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/reduced-abstraction-layer-framework.md
#   constructed abstraction : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/constructed-abstraction.md
#   direct abstraction : https://github.com/gratach/thoughts/blob/master/topics/graph/organizing/direct-abstraction.md
#   data concept : https://github.com/gratach/thoughts/blob/master/topics/data/graph/data-concept.md

from weakref import WeakValueDictionary

class neo4jRALFramework:
    def __init__(self, neo4j_session):
        self._neo4j_session = neo4j_session
        self._wrappersByAbstractionID = WeakValueDictionary()
    def _getAbstractionIdWrapper(self, abstractionID):
        wrapper = self._wrappersByAbstractionID.get(abstractionID)
        if wrapper == None:
            wrapper = Neo4jAbstraction(abstractionID, self)
            self._wrappersByAbstractionID[abstractionID] = wrapper
        return wrapper
    def ConstructedAbstraction(self, baseConnections):
        return ConstructedAbstraction(baseConnections, self)
    def DirectDataAbstraction(self, datastring, formatstring):
        return DirectDataAbstraction(datastring, formatstring, self)
    def DirectAbstraction(self, abstraction):
        return DirectAbstraction(abstraction, self)
    def InverseDirectAbstraction(self, directAbstraction):
        return InverseDirectAbstraction(directAbstraction, self)
    def deleteAbstraction(self, abstraction):
        deleteAbstraction(abstraction, self._neo4j_session)
    def getAbstractionType(self, abstraction):
        return getAbstractionType(abstraction.id, self)
    def getAbstractionContent(self, abstraction):
        type = self.getAbstractionType(abstraction)
        if type == "DirectDataAbstraction":
            return getDirectDataAbstractionContent(abstraction, self)
        elif type == "ConstructedAbstraction":
            return getBaseConnections(abstraction, self)
        elif type == "DirectAbstraction":
            return getDirectAbstractionContent(abstraction, self)
        elif type == "InverseDirectAbstraction":
            return getInverseDirectAbstractionContent(abstraction, self)
        else:
            raise ValueError("The abstraction type is not valid.")
    def searchRALJPattern(self, pattern):
        return searchRALJPattern(pattern, self)
    def listAllAbstractions(self):
        return listAllAbstractions(self)
    def getStringRepresentationFromAbstraction(self, abstracrion):
        return str(abstracrion.id)
    def getAbstractionFromStringRepresentation(self, representation):
        index = int(representation)
        # Check if the abstraction exists
        if not self._neo4j_session.run("MATCH (n:Abstraction) WHERE id(n) = $id RETURN id(n)", id=index).single():
            raise ValueError("The abstraction does not exist.")
        return self._getAbstractionIdWrapper(index)
    
class Neo4jAbstraction:
    """
    A wrapper class for the neo4j abstraction id.
    """
    def __init__(self, abstractionId, RALFramework):
        self._id = abstractionId
        self.RALFramework = RALFramework
        # Set remembered to false if not defined
        if isAbstractionRemembered(self, RALFramework) == None:
            RALFramework._neo4j_session.run("MATCH (n) WHERE id(n) = $id SET n.remember = false", id=self._id)
    
    @property
    def id(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return self._id
    @property
    def type(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return getAbstractionType(self._id, self.RALFramework)
    @property
    def data(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return getDirectDataAbstractionContent(self, self.RALFramework)[0] if self.type == "DirectDataAbstraction" else None
    @property
    def format(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return getDirectDataAbstractionContent(self, self.RALFramework)[1] if self.type == "DirectDataAbstraction" else None
    @property
    def baseConnections(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return getBaseConnections(self, self.RALFramework)[0] if self.type == "ConstructedAbstraction" else None
    @property
    def innerAbstraction(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return getDirectAbstractionContent(self, self.RALFramework) if self.type == "DirectAbstraction" else None
    @property
    def outerAbstraction(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return getInverseDirectAbstractionContent(self, self.RALFramework) if self.type == "InverseDirectAbstraction" else None
    # get remembered
    @property
    def remembered(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return isAbstractionRemembered(self, self.RALFramework)
    # set remembered
    @remembered.setter
    def remembered(self, value):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        assert type(value) == bool
        self.RALFramework._neo4j_session.run("MATCH (n) WHERE id(n) = $id SET n.remember = $value", id=self._id, value=value)
    def __del__(self):
        if self._id == None:
            return
        id = self.id
        self._id = None
        # Check if the abstraction can be savely deleted from the neo4j database
        idsToCheckForDeletion = set([id])
        while len(idsToCheckForDeletion) > 0:
            id = idsToCheckForDeletion.pop()
            idsToCheckForDeletion |= checkForSafeAbstractionDeletion(id, self.RALFramework)
    def forceDeletion(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        forcedDeletionIds = {self._id}
        safeDeletionIds = set()
        while len(forcedDeletionIds) > 0:
            id = forcedDeletionIds.pop()
            safeDeletionIds.add(id)
            forcedDeletionIds |= forceAbstractionDeletion(id, self.RALFramework).difference(safeDeletionIds)
        while len(safeDeletionIds) > 0:
            id = safeDeletionIds.pop()
            safeDeletionIds |= checkForSafeAbstractionDeletion(id, self.RALFramework)
    
    def __repr__(self):
        return "Abstraction(" + self.RALFramework.getStringRepresentationFromAbstraction(self) + ")"
    
def checkForSafeAbstractionDeletion(id, RALFramework):
    """
    Checks if the abstraction with the given id can be savely deleted from the neo4j database.
    Returns a set of the abstraction ids that should also be checked for safe deletion.
    """
    # Check if the abstraction is remembered
    if RALFramework._neo4j_session.run("MATCH (n) WHERE id(n) = $id RETURN n.remember", id=id).single().value():
        return set()
    # Check if tere is a active wrapper for the abstraction
    wrapper = RALFramework._wrappersByAbstractionID.get(id)
    if wrapper != None and wrapper._id != None:
        return set()
    # Check if there is a direct abstraction of the abstraction
    directAbstraction = RALFramework._neo4j_session.run("MATCH (n)-[:isAbstractionOf]->(m) WHERE id(m) = $id RETURN id(n)", id=id).single()
    if directAbstraction != None:
        return set()
    # Check if there is an inverse direct abstraction of the abstraction
    inverseDirectAbstraction = RALFramework._neo4j_session.run("MATCH (n)-[:isInverseAbstractionOf]->(m) WHERE id(m) = $id RETURN id(n)", id=id).single()
    if inverseDirectAbstraction != None:
        return set()
    # Get all the ids of the connected AbstractionTriples
    connectedTriples = set()
    for conn in ["subj", "pred", "obj"]:
        result = RALFramework._neo4j_session.run(f"MATCH (t:AbstractionTriple)-[:{conn}]->(n) WHERE id(n) = $id RETURN id(t)", id=id).value()
        for record in result:
            connectedTriples.add(record)
    # Check if all of the connected AbstractionTriples are owned by the removed abstraction
    ownedTriples = set(RALFramework._neo4j_session.run("MATCH (n)-[:ownsTriple]->(m) WHERE id(n) = $id RETURN id(m)", id=id).value())
    if connectedTriples != ownedTriples:
        return set()
    # Get all the ids of the connected abstractions
    connectedAbstractions = set()
    for triple in connectedTriples:
        for conn in ["subj", "pred", "obj"]:
            result = RALFramework._neo4j_session.run(f"MATCH (n)-[:{conn}]->(m) WHERE id(n) = $id RETURN id(m)", id=triple).value()
            for record in result:
                if record != id:
                    connectedAbstractions.add(record)
    # Get the id of the inner abstraction of the abstraction
    innerAbstraction = RALFramework._neo4j_session.run("MATCH (n)-[:isAbstractionOf]->(m) WHERE id(n) = $id RETURN id(m)", id=id).single()
    if innerAbstraction != None:
        connectedAbstractions.add(innerAbstraction.value())
    # Get the id of the outer abstraction of the abstraction
    outerAbstraction = RALFramework._neo4j_session.run("MATCH (n)-[:isInverseAbstractionOf]->(m) WHERE id(n) = $id RETURN id(m)", id=id).single()
    if outerAbstraction != None:
        connectedAbstractions.add(outerAbstraction.value())
    # Delete the owned AbstractionTriples
    for triple in ownedTriples:
        RALFramework._neo4j_session.run("MATCH (n) WHERE id(n) = $id DETACH DELETE n", id=triple)
    # Delete the abstraction
    RALFramework._neo4j_session.run("MATCH (n) WHERE id(n) = $id DETACH DELETE n", id=id)
    return connectedAbstractions

def forceAbstractionDeletion(id, RALFramework):
    """
    Forces the deletion of the abstraction with the given id from the neo4j database.
    returns the set of the abstraction ids that also have to be forced to be deleted.
    """
    # Unset the remembered flag
    RALFramework._neo4j_session.run("MATCH (n) WHERE id(n) = $id SET n.remember = false", id=id)
    # Deactivate the active wrapper for the abstraction if there is one
    wrapper = RALFramework._wrappersByAbstractionID.get(id)
    if wrapper != None:
        wrapper._id = None
    forcedDeletionIds = set()
    # Check if there is a direct abstraction of the abstraction
    directAbstraction = RALFramework._neo4j_session.run("MATCH (n)-[:isAbstractionOf]->(m) WHERE id(m) = $id RETURN id(n)", id=id).single()
    if directAbstraction != None:
        forcedDeletionIds.add(directAbstraction.value())
    # Check if there is an inverse direct abstraction of the abstraction
    inverseDirectAbstraction = RALFramework._neo4j_session.run("MATCH (n)-[:isInverseAbstractionOf]->(m) WHERE id(m) = $id RETURN id(n)", id=id).single()
    if inverseDirectAbstraction != None:
        forcedDeletionIds.add(inverseDirectAbstraction.value())
    # Get all the ids of the connected AbstractionTriples
    connectedTriples = set()
    for conn in ["subj", "pred", "obj"]:
        result = RALFramework._neo4j_session.run(f"MATCH (t:AbstractionTriple)-[:{conn}]->(n) WHERE id(n) = $id RETURN id(t)", id=id).value()
        for record in result:
            connectedTriples.add(record)
    # Add all the owners of the connected AbstractionTriples to the forcedDeletionIds
    for triple in connectedTriples:
        result = RALFramework._neo4j_session.run("MATCH (n)-[:ownsTriple]->(m) WHERE id(m) = $id RETURN id(n)", id=triple).single().value()
        if result != id:
            forcedDeletionIds.add(result)
    # Return the forcedDeletionIds
    return forcedDeletionIds

def ConstructedAbstraction(baseConnections, framework):
    """
    Creates an constructed abstraction in the neo4j database and returns the node id of the created constructed abstraction.
    """
    neo4j_session = framework._neo4j_session
    # Create the query string
    structureString = f"(n:ConstructedAbstraction:Abstraction {{connectionCount: {len(baseConnections)}}})"
    idDict = {}
    i = 0
    for connection in baseConnections:
        subj, pred, obj = connection
        if not 0 in connection:
            raise ValueError("The semantic connection must contain at least one None value.")
        if subj == 0:
            subj = "(n)"
        else:
            assert type(subj) == Neo4jAbstraction
            idDict[f"c{i}"] = subj.id
            subj = f"(c{i})"
            i += 1
        if pred == 0:
            pred = "(n)"
        else:
            assert type(pred) == Neo4jAbstraction
            idDict[f"c{i}"] = pred.id
            pred = f"(c{i})"
            i += 1
        if obj == 0:
            obj = "(n)"
        else:
            assert type(obj) == Neo4jAbstraction
            idDict[f"c{i}"] = obj.id
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
    return framework._getAbstractionIdWrapper(id)

def DirectDataAbstraction(datastring, formatstring, framework):
    """
    Creates the direct abstraction of a data concept in the neo4j database and returns the node id of the created direct abstraction.
    """
    neo4j_session = framework._neo4j_session
    id = neo4j_session.run("MERGE (a:DirectDataAbstraction:Abstraction {data: $data, format: $format}) RETURN id(a)", data=datastring, format=formatstring).single().value()
    return framework._getAbstractionIdWrapper(id)

def DirectAbstraction(abstraction, framework):
    """
    Creates the direct abstraction of an abstraction in the neo4j database and returns the node id of the created direct abstraction.
    """
    neo4j_session = framework._neo4j_session
    id = neo4j_session.run("MATCH (n) WHERE id(n) = $id MERGE (a:DirectAbstraction:Abstraction)-[:isAbstractionOf]->(n) RETURN id(a)", id=abstraction.id).single().value()
    return framework._getAbstractionIdWrapper(id)

def InverseDirectAbstraction(directAbstraction, framework):
    """
    Creates the inverse direct abstraction of an abstraction in the neo4j database and returns the node id of the created direct abstraction.
    """
    neo4j_session = framework._neo4j_session
    id = neo4j_session.run("MATCH (n) WHERE id(n) = $id MERGE (a:InverseDirectAbstraction:Abstraction)-[:isInverseAbstractionOf]->(n) RETURN id(a)", id=directAbstraction.id).single().value()
    return framework._getAbstractionIdWrapper(id)

def isAbstractionRemembered(abstraction, framework):
    """
    Returns whether the abstraction with the given id is remembered in the neo4j database.
    """
    neo4j_session = framework._neo4j_session
    return neo4j_session.run("MATCH (n) WHERE id(n) = $id RETURN n.remember", id=abstraction.id).single().value()

def getBaseConnections(abstraction, framework):
    """
    Returns the base connections of the abstraction with the given id.
    """
    neo4j_session = framework._neo4j_session
    id = abstraction.id
    ownedTriples = set(neo4j_session.run("MATCH (n)-[:ownsTriple]->(m) WHERE id(n) = $id RETURN id(m)", id=id).value())
    semanticConnections = []
    for triple in ownedTriples:
        subj = neo4j_session.run("MATCH (t)-[:subj]->(n) WHERE id(t) = $id RETURN id(n)", id=triple).single().value()
        pred = neo4j_session.run("MATCH (t)-[:pred]->(n) WHERE id(t) = $id RETURN id(n)", id=triple).single().value()
        obj = neo4j_session.run("MATCH (t)-[:obj]->(n) WHERE id(t) = $id RETURN id(n)", id=triple).single().value()
        semanticConnections.append((0 if subj == id else framework._getAbstractionIdWrapper(subj),
                                    0 if pred == id else framework._getAbstractionIdWrapper(pred), 
                                    0 if obj == id else framework._getAbstractionIdWrapper(obj)))
    return frozenset(semanticConnections)

def getAbstractionType(abstractionId, framework):
    """
    Returns the type of the abstraction with the given id.
    """
    neo4j_session = framework._neo4j_session
    type = neo4j_session.run("MATCH (n) WHERE id(n) = $id RETURN labels(n)", id=abstractionId).single().value()
    return set({"ConstructedAbstraction", "DirectDataAbstraction", "DirectAbstraction", "InverseDirectAbstraction"}).intersection(type).pop()

def getDirectDataAbstractionContent(abstraction, framework):
    """
    Returns the data and format of the direct abstraction with the given id.
    """
    neo4j_session = framework._neo4j_session
    data = neo4j_session.run("MATCH (n:DirectDataAbstraction) WHERE id(n) = $id RETURN n.data", id=abstraction.id).single().value()
    format = neo4j_session.run("MATCH (n:DirectDataAbstraction) WHERE id(n) = $id RETURN n.format", id=abstraction.id).single().value()
    return (data, format)

def getDirectAbstractionContent(abstraction, framework):
    """
    Returns the id of the abstraction that the direct abstraction with the given id is an abstraction of.
    """
    neo4j_session = framework._neo4j_session
    return framework._getAbstractionIdWrapper(neo4j_session.run("MATCH (n)-[:isAbstractionOf]->(m) WHERE id(n) = $id RETURN id(m)", id=abstraction.id).single().value())

def getInverseDirectAbstractionContent(abstraction, framework):
    """
    Returns the id of the abstraction that the inverse direct abstraction with the given id is an inverse abstraction of.
    """
    neo4j_session = framework._neo4j_session
    return framework._getAbstractionIdWrapper(neo4j_session.run("MATCH (n)-[:isInverseAbstractionOf]->(m) WHERE id(n) = $id RETURN id(m)", id=abstraction.id).single().value())

def searchRALJPattern(pattern, framework):
    """
    Searches for appearances of the given pattern in the neo4j database and returns a list of dictionaries that map the ids of the ralj pattern to the neo4j ids of the appearances.
    The pattern can also contain neo4j ids which are maked by enclosing them in square brackets.
    When searching for constructed concepts that can have more than the listed connections, a "+" has to be added at the end of the connection list.
    When searching for direct data concepts with unknown data or format, the data or format can be set to 0.
    """
    # TODO : replace id by wrapper
    neo4j_session = framework._neo4j_session
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
        for data, ref in datalist.items():
            dataAndFormat = ", ".join([*([] if type(data) == list else[f"data: '{data}'"]), *([] if type(format) == list else[f"format: '{format}'"])])
            if type(ref) == str:
                refName = "local" + ref.encode("utf-8").hex()
                localIDs.add(ref)
            elif type(ref) == Neo4jAbstraction:
                refName = "global" + str(ref.id)
                globalIDs.add(ref.id)
            else:
                raise ValueError("The id of a data concept must be an int or a list with one int.")
            structureStringArray.append(f"({refName}:DirectDataAbstraction {{{dataAndFormat}}})")
    # Evaluate the constructedConceptBlock
    tripelIndex = 0
    for ref, connections in constructedConceptBlock.items():
        if type(ref) == str:
            refName = "local" + ref.encode("utf-8").hex()
            localIDs.add(ref)
        elif type(ref) == Neo4jAbstraction:
            refName = "global" + str(ref.id)
            globalIDs.add(ref.id)
        else:
            raise ValueError("The id of a constructed concept must be an int or a list with one int.")
        if len(connections) > 0 and list(connections)[-1] == "+":
            connections = list(connections)[:-1]
            structureStringArray.append(f"({refName}:ConstructedAbstraction)")
        else:
            structureStringArray.append(f"({refName}:ConstructedAbstraction {{connectionCount: {len(connections)}}})")
        for connection in connections:
            structureStringArray.append(f"({refName})-[:ownsTriple]->(triple{tripelIndex}:AbstractionTriple)")
            for i, element in enumerate(connection):
                if element == 0:
                    structureStringArray.append(f"(triple{tripelIndex})-[:{['subj', 'pred', 'obj'][i]}]->({refName})")
                elif type(element) == str:
                    elementName = "local" + element.encode("utf-8").hex()
                    structureStringArray.append(f"(triple{tripelIndex})-[:{['subj', 'pred', 'obj'][i]}]->({elementName})")
                    localIDs.add(element)
                elif type(element) == Neo4jAbstraction:
                    elementName = "global" + str(element.id)
                    structureStringArray.append(f"(triple{tripelIndex})-[:{['subj', 'pred', 'obj'][i]}]->({elementName})")
                    globalIDs.add(element.id)
                else:
                    raise ValueError("The id of a triple concept must be an int or a list with one int.")
            tripelIndex += 1
    # Evaluate the directAbstractionBlock
    for ref, abstraction in directAbstractionBlock.items():
        if type(ref) == str:
            refName = "local" + ref.encode("utf-8").hex()
            localIDs.add(ref)
        elif type(ref) == Neo4jAbstraction:
            refName = "global" + str(ref.id)
            globalIDs.add(ref.id)
        else:
            raise ValueError("The id of a direct abstraction must be an int or a list with one int.")
        if type(abstraction) == str:
            abstractionName = "local" + abstraction.encode("utf-8").hex()
            structureStringArray.append(f"({refName}:DirectAbstraction)-[:isAbstractionOf]->({abstractionName})")
            localIDs.add(abstraction)
        elif type(abstraction) == Neo4jAbstraction:
            abstractionName = "global" + str(abstraction.id)
            structureStringArray.append(f"({refName}:DirectAbstraction)-[:isAbstractionOf]->({abstractionName})")
            globalIDs.add(abstraction.id)
        else:
            raise ValueError("The id of an abstraction must be an int or a list with one int.")
    # Evaluate the inverseDirectAbstractionBlock
    for ref, abstraction in inverseDirectAbstractionBlock.items():
        if type(ref) == str:
            refName = "local" + ref.encode("utf-8").hex()
            localIDs.add(ref)
        elif type(ref) == Neo4jAbstraction:
            refName = "global" + str(ref.id)
            globalIDs.add(ref.id)
        else:
            raise ValueError("The id of an inverse direct abstraction must be an int or a list with one int.")
        if type(abstraction) == str:
            abstractionName = "local" + abstraction.encode("utf-8").hex()
            structureStringArray.append(f"({refName}:InverseDirectAbstraction)-[:isInverseAbstractionOf]->({abstractionName})")
            localIDs.add(abstraction)
        elif type(abstraction) == Neo4jAbstraction:
            abstractionName = "global" + str(abstraction.id)
            structureStringArray.append(f"({refName}:InverseDirectAbstraction)-[:isInverseAbstractionOf]->({abstractionName})")
            globalIDs.add(abstraction.id)
        else:
            raise ValueError("The id of an abstraction must be an int or a list with one int.")
    # Create the query string
    structureString = "MATCH " + ", ".join(structureStringArray)
    if len(globalIDs) > 0:
        structureString += " WHERE " +  " AND ".join([f"id(global{id}) = {id}" for id in globalIDs])
    if len(localIDs) == 0:
        raise ValueError("The pattern must contain at least one local id.")
    localIDs = list(localIDs)
    structureString += " RETURN " + ", ".join([f"id(local{id.encode('utf-8').hex()})" for id in localIDs])
    # Execute the query and return the result as a list of dictionaries
    result = neo4j_session.run(structureString).values()
    result = [dict(zip(localIDs, [framework._getAbstractionIdWrapper(absId) for absId in record])) for record in result]
    return result

def listAllAbstractions(framework):
    """
    Returns a list of all abstractions in the neo4j database.
    """
    neo4j_session = framework._neo4j_session
    result = neo4j_session.run("MATCH (n:Abstraction) RETURN id(n)").value()
    return [framework._getAbstractionIdWrapper(id) for id in result]