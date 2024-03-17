# Load and save data from RALJ files into the neo4j database.
# RALJ format documentation:
#   https://github.com/gratach/thoughts/blob/master/topics/data/graph/reduced-abstraction-layer-json.md

import json
from .neo4jabstractions import *

def load_ralj_file(file_path, neo4j_session):
    with open(file_path, "r") as file:
        data = json.load(file)
    return load_ralj_data(data, neo4j_session)

def load_ralj_data(data, neo4j_session):
    assert type(data) == list and len(data) == 3
    dataConceptBlock = data[0]
    constructedConceptBlock = data[1]
    directAbstractionBlock = data[2]
    abstractionIDByJsonNodeID = {}
    relatingAbstractionsByJsonNodeID = {}
    uncheckedJsonNodeIDs = set(constructedConceptBlock.keys()).union(set(directAbstractionBlock.keys()))
    loadedJsonNodeIDs = set()
    # Load all direct data abstractions
    for format, dataConcepts in dataConceptBlock.items():
        for data, jsonNodeID in dataConcepts.items():
            abstractionIDByJsonNodeID[jsonNodeID] = DirectDataAbstraction(data, format, neo4j_session)
            loadedJsonNodeIDs.add(jsonNodeID)
    # Load all constructed abstractions
    while len(uncheckedJsonNodeIDs) > 0:
        jsonNodeID = uncheckedJsonNodeIDs.pop()
        if jsonNodeID in directAbstractionBlock:
            # The abstraction is a direct abstraction
            innerJsonNodeID = directAbstractionBlock[jsonNodeID]
            if innerJsonNodeID not in loadedJsonNodeIDs:
                if innerJsonNodeID not in relatingAbstractionsByJsonNodeID:
                    relatingAbstractionsByJsonNodeID[innerJsonNodeID] = set()
                relatingAbstractionsByJsonNodeID[innerJsonNodeID].add(jsonNodeID)
                continue
            abstractionIDByJsonNodeID[jsonNodeID] = DirectAbstraction(abstractionIDByJsonNodeID[innerJsonNodeID], neo4j_session)
            loadedJsonNodeIDs.add(jsonNodeID)
        else:
            # The abstraction is a constructed abstraction
            semanticConnections = constructedConceptBlock[jsonNodeID]
            allConnectedJsonNodeIDsLoaded = True
            for connection in semanticConnections:
                for connectedJsonNodeID in connection:
                    if connectedJsonNodeID != 0 and connectedJsonNodeID not in loadedJsonNodeIDs:
                        allConnectedJsonNodeIDsLoaded = False
                        if connectedJsonNodeID not in relatingAbstractionsByJsonNodeID:
                            relatingAbstractionsByJsonNodeID[connectedJsonNodeID] = set()
                        relatingAbstractionsByJsonNodeID[connectedJsonNodeID].add(jsonNodeID)
                        break
                if not allConnectedJsonNodeIDsLoaded:
                    break
            if allConnectedJsonNodeIDsLoaded:
                # Load the abstraction
                semanticConnections = [[None if y == 0 else abstractionIDByJsonNodeID[y] for y in x] for x in semanticConnections]
                abstractionIDByJsonNodeID[jsonNodeID] = ConstructedAbstraction(semanticConnections, neo4j_session)
                loadedJsonNodeIDs.add(jsonNodeID)
            else:
                continue
        # The abstraction is loaded
        if jsonNodeID in relatingAbstractionsByJsonNodeID:
            for relatingJsonNodeID in relatingAbstractionsByJsonNodeID[jsonNodeID]:
                if not relatingJsonNodeID in loadedJsonNodeIDs:
                    uncheckedJsonNodeIDs.add(relatingJsonNodeID)
            del relatingAbstractionsByJsonNodeID[jsonNodeID]
    return set(abstractionIDByJsonNodeID.values())

def save_ralj_file(file_path, neo4j_session):
    with open(file_path, "w") as file:
        data = save_ralj_data(neo4j_session)
        json.dump(data, file)

def save_ralj_data(abstractions, neo4j_session):
    jsonNodeIDByAbstractionID = {}
    relatingAbstractionsByAbstractionID = {}
    uncheckedAbstractions = set(abstractions)
    savedAbstractions = set()
    jsonNodeIndex = 1
    dataConceptBlock = {}
    constructedConceptBlock = {}
    directAbstractionBlock = {}
    while len(uncheckedAbstractions) > 0:
        abstraction = uncheckedAbstractions.pop()
        abstractionType = getAbstractionType(abstraction, neo4j_session)
        if abstractionType == "DirectDataAbstraction":
            data, format = getDirectDataAbstractionContent(abstraction, neo4j_session)
            if format not in dataConceptBlock:
                dataConceptBlock[format] = {}
            if data not in dataConceptBlock[format]:
                dataConceptBlock[format][data] = jsonNodeIndex
                jsonNodeIDByAbstractionID[abstraction] = jsonNodeIndex
                jsonNodeIndex += 1
        elif abstractionType == "ConstructedAbstraction":
            # Check if all connected abstractions are saved
            semanticConnections = getSemanticConnections(abstraction, neo4j_session)
            allConnectedAbstractionsSaved = True
            for connection in semanticConnections:
                for connectedAbstraction in connection:
                    if connectedAbstraction != None and connectedAbstraction not in savedAbstractions:
                        uncheckedAbstractions.add(connectedAbstraction)
                        allConnectedAbstractionsSaved = False
                        # Add the relating abstraction
                        if connectedAbstraction not in relatingAbstractionsByAbstractionID:
                            relatingAbstractionsByAbstractionID[connectedAbstraction] = set()
                        relatingAbstractionsByAbstractionID[connectedAbstraction].add(abstraction)
                        break
                if not allConnectedAbstractionsSaved:
                    break
            if allConnectedAbstractionsSaved:
                # Save the abstraction
                jsonNodeIDByAbstractionID[abstraction] = jsonNodeIndex
                jsonSemanticConnections = [[0 if y == None else jsonNodeIDByAbstractionID[y] for y in x] for x in semanticConnections]
                constructedConceptBlock[jsonNodeIndex] = jsonSemanticConnections
                jsonNodeIndex += 1
            else:
                continue
        elif abstractionType == "DirectAbstraction":
            innerAbstraction = getDirectAbstractionContent(abstraction, neo4j_session)
            if innerAbstraction not in savedAbstractions:
                uncheckedAbstractions.add(innerAbstraction)
                # Add the relating abstraction
                if innerAbstraction not in relatingAbstractionsByAbstractionID:
                    relatingAbstractionsByAbstractionID[innerAbstraction] = set()
                relatingAbstractionsByAbstractionID[innerAbstraction].add(abstraction)
                continue
            else:
                # Save the direct abstraction
                jsonNodeIDByAbstractionID[abstraction] = jsonNodeIndex
                directAbstractionBlock[jsonNodeIndex] = jsonNodeIDByAbstractionID[innerAbstraction]
                jsonNodeIndex += 1
        # The abstraction is saved
        savedAbstractions.add(abstraction)
        # Add the relating abstractions
        if abstraction in relatingAbstractionsByAbstractionID:
            for relatingAbstraction in relatingAbstractionsByAbstractionID[abstraction]:
                if not relatingAbstraction in savedAbstractions:
                    uncheckedAbstractions.add(relatingAbstraction)
            del relatingAbstractionsByAbstractionID[abstraction]
    return [dataConceptBlock, constructedConceptBlock, directAbstractionBlock]