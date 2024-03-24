

def RalID(context, idString, baseConnections = set()):
    """
    Get the constructed abstraction of an identified concept
    """
    RALFramework = context.get("RALFramework")
    identifiedBy = loadContextConcept(context, "identifiedBy", lambda : RALFramework.DirectDataAbstraction("identifiedBy", "atomic"))
    ralidString = loadContextConcept(context, "ralid_" +  idString, lambda: RALFramework.DirectDataAbstraction(idString, "ralid"))
    if len(baseConnections) == 0:
        return loadContextConcept(context, "identified_" + idString, lambda: RALFramework.ConstructedAbstraction({(0, identifiedBy, ralidString)}))
    return RALFramework.ConstructedAbstraction({(0, identifiedBy, ralidString)}|baseConnections)

def RalText(context, text):
    """
    Get the constructed abstraction of a text
    """
    RALFramework = context.get("RALFramework")
    return RALFramework.DirectDataAbstraction(text, "text")

def RalLanguage(context, languageIdString):
    """
    Get the constructed abstraction of a language
    """
    RALFramework = context.get("RALFramework")
    isInstanceOf = RalID(context, "isInstanceOf")
    languageID = RalID(context, "language")
    return loadContextConcept(context, "language_" + languageIdString, lambda: RalID(context, languageIdString, {(0, isInstanceOf, languageID)}))

def RalTerm(context, termString, language = None):
    """
    Get the constructed abstraction of a term
    """
    RALFramework = context.get("RALFramework")
    isTermOfLanguage = RalID(context, "isTermOfLanguage")
    hasTextContent = RalID(context, "hasTextContent")
    if language == None:
        language = RalLanguage(context, "lang.english")
    return RALFramework.ConstructedAbstraction({(0, isTermOfLanguage, language), (0, hasTextContent, RalText(context, termString))})

def RealWorldConcept(context, baseConnections = set(), name = [], connectionName = [], inverseConnectionName = [], language = None):
    """
    Get the constructed abstraction of a term concept
    """
    RALFramework = context.get("RALFramework")
    names = name if type(name) in [list, set, tuple] else [name]
    names = {name if RALFramework.isValidAbstraction(name) else RalTerm(context, name, language) for name in names}
    relationNames = connectionName if type(connectionName) in [list, set, tuple] else [connectionName]
    relationNames = {relationName if RALFramework.isValidAbstraction(relationName) else RalTerm(context, relationName, language) for relationName in relationNames}
    inverseRelationNames = inverseConnectionName if type(inverseConnectionName) in [list, set, tuple] else [inverseConnectionName]
    inverseRelationNames = {inverseRelationName if RALFramework.isValidAbstraction(inverseRelationName) else RalTerm(context, inverseRelationName, language) for inverseRelationName in inverseRelationNames}
    isInstanceOf = RalID(context, "isInstanceOf")
    realWorldConcept = RalID(context, "realWorldConcept")
    isCalled = RalID(context, "isCalled")
    relationIsCalled = RalID(context, "relationIsCalled")
    inverseRelationIsCalled = RalID(context, "inverseRelationIsCalled")
    return RALFramework.ConstructedAbstraction({(0, isInstanceOf, realWorldConcept)}|{(0, isCalled, name) for name in names}|{(0, relationIsCalled, relationName) for relationName in relationNames}|{(0, inverseRelationIsCalled, inverseRelationName) for inverseRelationName in inverseRelationNames}|baseConnections)

def loadContextConcept(context, conceptName, conceptCreationFunction):
    """
    Load a concept from the context if it exists, otherwise create it
    """
    concepts = context["concepts"] = context.get("concepts", {})
    if conceptName in concepts:
        return concepts[conceptName]
    concept = conceptCreationFunction()
    concepts[conceptName] = concept
    return concept