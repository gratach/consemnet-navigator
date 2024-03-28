

_identifiedByKeyObject = object()
_ralidStringKeyObject = object()
def RalID(RALFramework, idString, baseConnections = set(), tempStorageDict = None):
    """
    Get the constructed abstraction of an identified concept
    """
    identifiedBy = loadTempStorageConcept(_identifiedByKeyObject, tempStorageDict, RALFramework, lambda : RALFramework.DirectDataAbstraction("identifiedBy", "atomic"))
    ralidString = loadTempStorageConcept((_ralidStringKeyObject, idString), tempStorageDict, RALFramework, lambda: RALFramework.DirectDataAbstraction(idString, "ralid"))
    if len(baseConnections) == 0:
        return loadTempStorageConcept((_identifiedByKeyObject, idString), tempStorageDict, RALFramework, lambda: RALFramework.ConstructedAbstraction({(0, identifiedBy, ralidString)}))
    return RALFramework.ConstructedAbstraction({(0, identifiedBy, ralidString)}|baseConnections)

def RalText(RALFramework, text, tempStorageDict = None):
    """
    Get the constructed abstraction of a text
    """
    return RALFramework.DirectDataAbstraction(text, "text")

_languageKeyObject = object()
def RalLanguage(RALFramework, languageIdString, tempStorageDict = None):
    """
    Get the constructed abstraction of a language
    """
    isInstanceOf = RalID(RALFramework, "isInstanceOf", tempStorageDict = tempStorageDict)
    languageID = RalID(RALFramework, "language", tempStorageDict = tempStorageDict)
    return loadTempStorageConcept((_languageKeyObject, languageIdString), tempStorageDict, RALFramework, lambda: RalID(RALFramework, languageIdString, {(0, isInstanceOf, languageID)}, tempStorageDict = tempStorageDict))

def RalTerm(RALFramework, termString, language = None, tempStorageDict = None):
    """
    Get the constructed abstraction of a term
    """
    isTermOfLanguage = RalID(RALFramework, "isTermOfLanguage", tempStorageDict = tempStorageDict)
    hasTextContent = RalID(RALFramework, "hasTextContent", tempStorageDict = tempStorageDict)
    if language == None:
        language = RalLanguage(RALFramework, "lang.english", tempStorageDict = tempStorageDict)
    return RALFramework.ConstructedAbstraction({(0, isTermOfLanguage, language), (0, hasTextContent, RalText(RALFramework, termString, tempStorageDict = tempStorageDict))})

def RealWorldConcept(RALFramework, baseConnections = set(), name = [], connectionName = [], inverseConnectionName = [], language = None, tempStorageDict = None):
    """
    Get the constructed abstraction of a term concept
    """
    names = name if type(name) in [list, set, tuple] else [name]
    names = {name if RALFramework.isValidAbstraction(name) else RalTerm(RALFramework, name, language, tempStorageDict=tempStorageDict) for name in names}
    relationNames = connectionName if type(connectionName) in [list, set, tuple] else [connectionName]
    relationNames = {relationName if RALFramework.isValidAbstraction(relationName) else RalTerm(RALFramework, relationName, language, tempStorageDict=tempStorageDict) for relationName in relationNames}
    inverseRelationNames = inverseConnectionName if type(inverseConnectionName) in [list, set, tuple] else [inverseConnectionName]
    inverseRelationNames = {inverseRelationName if RALFramework.isValidAbstraction(inverseRelationName) else RalTerm(RALFramework, inverseRelationName, language, tempStorageDict=tempStorageDict) for inverseRelationName in inverseRelationNames}
    isInstanceOf = RalID(RALFramework, "isInstanceOf", tempStorageDict=tempStorageDict)
    realWorldConcept = RalID(RALFramework, "realWorldConcept", tempStorageDict=tempStorageDict)
    isCalled = RalID(RALFramework, "isCalled", tempStorageDict=tempStorageDict)
    relationIsCalled = RalID(RALFramework, "relationIsCalled", tempStorageDict=tempStorageDict)
    inverseRelationIsCalled = RalID(RALFramework, "inverseRelationIsCalled", tempStorageDict=tempStorageDict)
    return RALFramework.ConstructedAbstraction({(0, isInstanceOf, realWorldConcept)}|{(0, isCalled, name) for name in names}|{(0, relationIsCalled, relationName) for relationName in relationNames}|{(0, inverseRelationIsCalled, inverseRelationName) for inverseRelationName in inverseRelationNames}|baseConnections)

def findConceptName(RALFramework, concept, tempStorageDict = None):
    """
    Get the name of a concept
    """
    isCalled = RalID(RALFramework, "isCalled", tempStorageDict = tempStorageDict)
    res = [*RALFramework.searchRALJPattern(constructed = {concept : [[0, isCalled, "1"], "+"]})]
    if len(res) == 0:
        return None
    term = res[0]["1"]
    hasTextContent = RalID(RALFramework, "hasTextContent", tempStorageDict = tempStorageDict)
    res = [*RALFramework.searchRALJPattern(constructed = {term : [[0, hasTextContent, "1"], "+"]})]
    if len(res) == 0:
        return None
    return res[0]["1"].data

def findConceptsName(RALFramework, concepts, tempStorageDict = None):
    """
    Get the first valid name of a set of concepts
    """
    for concept in concepts:
        name = findConceptName(RALFramework, concept, tempStorageDict = tempStorageDict)
        if name != None:
            return name

def loadTempStorageConcept(conceptKey, tempstorage, ralFramework, conceptCreationFunction):
    """
    Load a concept from the context if it exists, otherwise create it
    """
    if tempstorage == None:
        return conceptCreationFunction()
    if conceptKey in tempstorage and ralFramework in tempstorage[conceptKey]:
        return tempstorage[conceptKey][ralFramework]
    concept = conceptCreationFunction()
    tempstorage.setdefault(conceptKey, {})[ralFramework] = concept
    return concept