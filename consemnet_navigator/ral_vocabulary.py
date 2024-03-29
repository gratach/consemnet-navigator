

_identifiedByKeyObject = object()
_ralidStringKeyObject = object()
def RalID(RALFramework, idString, baseConnections = set()):
    """
    Get the constructed abstraction of an identified concept
    """
    identifiedBy = loadLongTermStorageConcept(_identifiedByKeyObject, RALFramework, lambda : RALFramework.DirectDataAbstraction("identifiedBy", "atomic"))
    ralidString = loadLongTermStorageConcept((_ralidStringKeyObject, idString), RALFramework, lambda: RALFramework.DirectDataAbstraction(idString, "ralid"))
    if len(baseConnections) == 0:
        return loadLongTermStorageConcept((_identifiedByKeyObject, idString),  RALFramework, lambda: RALFramework.ConstructedAbstraction({(0, identifiedBy, ralidString)}))
    return RALFramework.ConstructedAbstraction({(0, identifiedBy, ralidString)}|baseConnections)

def RalText(RALFramework, text):
    """
    Get the constructed abstraction of a text
    """
    return RALFramework.DirectDataAbstraction(text, "text")

_languageKeyObject = object()
def RalLanguage(RALFramework, languageIdString):
    """
    Get the constructed abstraction of a language
    """
    isInstanceOf = RalID(RALFramework, "isInstanceOf")
    languageID = RalID(RALFramework, "language")
    return loadLongTermStorageConcept((_languageKeyObject, languageIdString),  RALFramework, lambda: RalID(RALFramework, languageIdString, {(0, isInstanceOf, languageID)}))

def RalTerm(RALFramework, termString, language = None):
    """
    Get the constructed abstraction of a term
    """
    isTermOfLanguage = RalID(RALFramework, "isTermOfLanguage")
    hasTextContent = RalID(RALFramework, "hasTextContent")
    if language == None:
        language = RalLanguage(RALFramework, "lang.english")
    return RALFramework.ConstructedAbstraction({(0, isTermOfLanguage, language), (0, hasTextContent, RalText(RALFramework, termString))})

def RealWorldConcept(RALFramework, baseConnections = set(), name = [], connectionName = [], inverseConnectionName = [], language = None):
    """
    Get the constructed abstraction of a term concept
    """
    names = name if type(name) in [list, set, tuple] else [name]
    names = {name if RALFramework.isValidAbstraction(name) else RalTerm(RALFramework, name, language) for name in names}
    relationNames = connectionName if type(connectionName) in [list, set, tuple] else [connectionName]
    relationNames = {relationName if RALFramework.isValidAbstraction(relationName) else RalTerm(RALFramework, relationName, language) for relationName in relationNames}
    inverseRelationNames = inverseConnectionName if type(inverseConnectionName) in [list, set, tuple] else [inverseConnectionName]
    inverseRelationNames = {inverseRelationName if RALFramework.isValidAbstraction(inverseRelationName) else RalTerm(RALFramework, inverseRelationName, language) for inverseRelationName in inverseRelationNames}
    isInstanceOf = RalID(RALFramework, "isInstanceOf")
    realWorldConcept = RalID(RALFramework, "realWorldConcept")
    isCalled = RalID(RALFramework, "isCalled")
    relationIsCalled = RalID(RALFramework, "relationIsCalled")
    inverseRelationIsCalled = RalID(RALFramework, "inverseRelationIsCalled")
    return RALFramework.ConstructedAbstraction({(0, isInstanceOf, realWorldConcept)}|{(0, isCalled, name) for name in names}|{(0, relationIsCalled, relationName) for relationName in relationNames}|{(0, inverseRelationIsCalled, inverseRelationName) for inverseRelationName in inverseRelationNames}|baseConnections)

def findConceptName(RALFramework, concept):
    """
    Get the name of a concept
    """
    isCalled = RalID(RALFramework, "isCalled")
    res = [*RALFramework.searchRALJPattern(constructed = {concept : [[0, isCalled, "1"], "+"]})]
    if len(res) == 0:
        return None
    term = res[0]["1"]
    hasTextContent = RalID(RALFramework, "hasTextContent")
    res = [*RALFramework.searchRALJPattern(constructed = {term : [[0, hasTextContent, "1"], "+"]})]
    if len(res) == 0:
        return None
    return res[0]["1"].data

def findConceptsName(RALFramework, concepts):
    """
    Get the first valid name of a set of concepts
    """
    for concept in concepts:
        name = findConceptName(RALFramework, concept)
        if name != None:
            return name

longTermStorageDict = {}
def loadLongTermStorageConcept(conceptKey, ralFramework, conceptCreationFunction):
    """
    Load a concept with a given key if it exists, otherwise create it
    """
    if conceptKey in longTermStorageDict and ralFramework in longTermStorageDict[conceptKey]:
        return longTermStorageDict[conceptKey][ralFramework]
    concept = conceptCreationFunction()
    longTermStorageDict.setdefault(conceptKey, {})[ralFramework] = concept
    ralFramework.onClose.add(removeRALFrameworkFromLongTermStorage)
    return concept

def removeRALFrameworkFromLongTermStorage(ralFramework):
    """
    Remove a RAL framework from long term storage
    """
    for key in longTermStorageDict:
        if ralFramework in longTermStorageDict[key]:
            del longTermStorageDict[key][ralFramework]