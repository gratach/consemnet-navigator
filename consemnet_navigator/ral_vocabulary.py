

def RalID(RALFramework, idString, baseConnections = set()):
    """
    Get the constructed abstraction of an identified concept
    """
    identifiedBy = RALFramework.DirectDataAbstraction("identifiedBy", "atomic")
    ralidString = RALFramework.DirectDataAbstraction("ralid", idString)
    return RALFramework.ConstructedAbstraction({(0, identifiedBy, ralidString)}|baseConnections)

def RalText(RALFramework, text):
    """
    Get the constructed abstraction of a text
    """
    return RALFramework.DirectDataAbstraction(text, "text")

def RalLanguage(RALFramework, languageIdString):
    """
    Get the constructed abstraction of a language
    """
    isInstanceOf = RalID( RALFramework, "isInstanceOf")
    languageID = RalID(RALFramework, "language")
    return RalID(RALFramework, languageIdString, {(0, isInstanceOf, languageID)})

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