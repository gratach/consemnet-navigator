from .network_tools import getIndirectConnections
from .ral_vocabulary import *
import json

def runNavigator(context):
    # Repeat while there is no navigator exit signal
    while not context.get("navigatorExit"):
        # Check if there is a current navigator session
        navigatorSession = context.get("navigatorSession")
        if navigatorSession == None:
            # Create a new navigator session
            navigatorSession = runNavigatorSession
            context["navigatorSession"] = navigatorSession
        # Run the navigator session
        navigatorSession(context.get("navigatorSessionContext", context))

def runNavigatorSession(context):
    # Check if there is an environment display function
    displayEnvironment = context.get("displayEnvironment")
    if displayEnvironment == None:
        # Create a new environment display function
        displayEnvironment = runDisplayAbstractionEnvironment
        context["displayEnvironment"] = displayEnvironment
    # Display the environment
    displayEnvironment(context.get("displayEnvironmentContext", context))
    # Check if there is a navigator input function
    navigatorInput = context.get("navigatorInput")
    if navigatorInput == None:
        # Create a new navigator input function
        navigatorInput = runNavigatorInput
        context["navigatorInput"] = navigatorInput
    # Get the navigator input
    navigatorInput(context.get("navigatorInputContext", context))

def runDisplayAbstractionEnvironment(context):
    print()
    # Check if there is a current abstraction
    currentAbstraction = context.get("currentAbstraction")
    if currentAbstraction == None:
        # Create a new current abstraction
        currentAbstraction = getCurrentAbstraction(context.get("getCurrentAbstractionContext", context))
        context["currentAbstraction"] = currentAbstraction
    # Check if there is a get abstraction name function
    getAbstractionName = context.get("getAbstractionName")
    if getAbstractionName == None:
        # Create a new get abstraction name function
        getAbstractionName = runGetAbstractionName
        context["getAbstractionName"] = getAbstractionName
    # Print the abstraction name
    abstractionName = getAbstractionName(currentAbstraction, context.get("getAbstractionNameContext", context))
    print(abstractionName)
    # Get the base connections of the current abstraction
    RF = context.get("RALFramework")
    abstractionType = RF.getAbstractionType(currentAbstraction)
    if abstractionType == "DirectDataAbstraction":
        data, format = RF.getAbstractionContent(currentAbstraction)
        print("Data: " + data)
        print("Format: " + format)
    elif abstractionType == "DirectAbstraction":
        innerAbstraction = RF.getAbstractionContent(currentAbstraction)
        print("Inner abstraction: " + getAbstractionName(innerAbstraction, context.get("getAbstractionNameContext", context)))
    elif abstractionType == "InverseDirectAbstraction":
        innerAbstraction = RF.getAbstractionContent(currentAbstraction)
        print("Inner abstraction: " + getAbstractionName(innerAbstraction, context.get("getAbstractionNameContext", context)))
    elif abstractionType == "ConstructedAbstraction":
        baseConnections = RF.getAbstractionContent(currentAbstraction)
        # Print the base connections
        print("Base connections: [")
        for connection in baseConnections:
            print("    [" + ", ".join([" - " if x == 0 else getAbstractionName(x, context.get("getAbstractionNameContext", context)) for x in connection]) + "],")
        print("]")
    print("Indirect connections: [")
    # Get the indirect connections of the current abstraction
    indirectConnections = getIndirectConnections(currentAbstraction, RF)
    # Print the indirect connections
    for connection in indirectConnections:
        print("    [" + ", ".join([" - " if x == None else getAbstractionName(x, context.get("getAbstractionNameContext", context)) for x in connection]) + "],")
    print("]")

def runNavigatorInput(context):
    # Get the input
    textinput = input("Enter Prompt: ")
    # Get the list of the prompts
    navigatorPrompts = context.get("navigatorPrompts")
    if navigatorPrompts == None:
        # Create a new list of prompts
        navigatorPrompts = [
            {
                "tryPrompt" : tryNavigateToIndex,
                "description" : "Navigate to the abstraction with the given index.",
                "keyword" : "<number>",
            },
            {
                "tryPrompt" : tryGetNavigatorHelp,
                "description" : "Display the navigator help.",
                "keyword" : "help"
            },
            {
                "tryPrompt" : tryExitNavigator,
                "description" : "Exit the navigator.",
                "keyword" : "exit"
            },
            {
                "tryPrompt" : trySearchRALJPattern,
                "description" : "Search the RALJ pattern.",
                "keyword" : "search"
            }
        ]
        context["navigatorPrompts"] = navigatorPrompts
    # Check the input against the prompts
    for prompt in navigatorPrompts:
        if prompt["tryPrompt"](textinput, context):
            return
    print("Invalid input.")
    input("OK")

def getCurrentAbstraction(context):
    # Get a list of all abstractions
    RF = context.get("RALFramework")
    abstractions = RF.listAllAbstractions()
    if len(abstractions) == 0:
        return 0
    return abstractions[0]

def runGetAbstractionName(abstraction, context):
    RF = context.get("RALFramework")
    return RF.getStringRepresentationFromAbstraction(abstraction)

def tryNavigateToIndex(textinput, context):
    # Check if there is an abstraction for the given index
    RF = context.get("RALFramework")
    try:
        context["currentAbstraction"] = RF.getAbstractionFromStringRepresentation(textinput)
        return True
    except:
        return False

def tryGetNavigatorHelp(textinput, context):
    if not textinput == "help":
        return False
    print()
    # Get the list of prompts
    navigatorPrompts = context.get("navigatorPrompts")
    # Print the prompts
    print("Navigator Help:")
    for prompt in navigatorPrompts:
        print(prompt["keyword"] + ": " + prompt["description"])
    input("OK")
    return True

def tryExitNavigator(textinput, context):
    if not textinput == "exit":
        return False
    context["navigatorExit"] = True
    return True

def trySearchRALJPattern(textinput, context):
    if not textinput == "search":
        return False
    pattern = input("Enter Pattern: ")
    # Check if the input is a pattern
    try:
        pattern = json.loads(pattern)
    except:
        print("Invalid json.")
        input("OK")
        return True
    RF = context.get("RALFramework")
    try:
        result = RF.searchRALJPattern(pattern)
    except:
        print("Invalid pattern.")
        input("OK")
        return True
    print("Result: " + str(result))


def runDisplayRealWorldConceptEnvironment(context):
    print()
    RF = context.get("RALFramework")
    # Check if there is a current abstraction
    currentAbstraction = context.get("currentAbstraction")
    if currentAbstraction == None:
        # Create a new current abstraction
        currentAbstraction = getCurrentAbstraction(context.get("getCurrentAbstractionContext", context))
        context["currentAbstraction"] = currentAbstraction
    # Check if there is a getAbstractionGroup function
    getAbstractionGroup = context.get("getAbstractionGroup")
    if getAbstractionGroup == None:
        # Create a new getAbstractionGroup function
        getAbstractionGroup = runGetAbstractionGroup
        context["getAbstractionGroup"] = getAbstractionGroup
    # Get the abstraction group
    abstractionGroup = getAbstractionGroup(currentAbstraction, context.get("getAbstractionGroupContext", context))
    # Get the name of the abstraction group
    abstractionGroupName = findConceptsName(RF, abstractionGroup)
    context["currentAbstractionTerm"] = abstractionGroupName
    print(abstractionGroupName + " " + RF.getStringRepresentationFromAbstraction(currentAbstraction))
    # Get the base connections of the current abstraction
    connectionByConnectionName = {} # {connectionName : [connection, inverseConnection, {connectedAbstractionName : connectedAbstraction}]}
    isInstanceOf = RalID(RF, "isInstanceOf")
    realWorldConcept = RalID(RF, "realWorldConcept")
    isCalled = RalID(RF, "isCalled")
    relationIsCalled = RalID(RF, "relationIsCalled")
    inverseRelationIsCalled = RalID(RF, "inverseRelationIsCalled")
    hasTextContent = RalID(RF, "hasTextContent")
    for abstraction in abstractionGroup:
        connections = RF.searchRALJPattern(triples = [(abstraction, "connection", "connectedAbstraction"), 
                                                      ("connection", isInstanceOf, realWorldConcept), ("connectedAbstraction", isInstanceOf, realWorldConcept),
                                                      ("connection", relationIsCalled, "connectionTerm"), ("connectionTerm", hasTextContent, "connectionName"),
                                                      ("connectedAbstraction", isCalled, "connectedAbstractionTerm"), ("connectedAbstractionTerm", hasTextContent, "connectedAbstractionName")])
        for connection in connections:
            connectionName = connection["connectionName"].data
            if not connectionName in connectionByConnectionName:
                connectionByConnectionName[connectionName] = [None, None, {}]
            connectionByConnectionName[connectionName][0] = connection["connection"]
            connectionByConnectionName[connectionName][2][connection["connectedAbstractionName"].data] = connection["connectedAbstraction"]
        inverseConnections = RF.searchRALJPattern(triples = [("connectedAbstraction", "inverseConnection", abstraction), 
                                                           ("inverseConnection", isInstanceOf, realWorldConcept), ("connectedAbstraction", isInstanceOf, realWorldConcept),
                                                           ("inverseConnection", inverseRelationIsCalled, "connectionTerm"), ("connectionTerm", hasTextContent, "connectionName"),
                                                           ("connectedAbstraction", isCalled, "connectedAbstractionTerm"), ("connectedAbstractionTerm", hasTextContent, "connectedAbstractionName")])
        for connection in inverseConnections:
            connectionName = connection["connectionName"].data
            if not connectionName in connectionByConnectionName:
                connectionByConnectionName[connectionName] = [None, None, {}]
            connectionByConnectionName[connectionName][1] = connection["inverseConnection"]
            connectionByConnectionName[connectionName][2][connection["connectedAbstractionName"].data] = connection["connectedAbstraction"]
    # Sort the connections by connection name
    connectionNames = list(connectionByConnectionName.keys())
    connectionNames.sort(key = lambda x: (x[1].upper(), x[1]))
    # Print the connections
    for connectionName in connectionNames:
        connection, inverseConnection, connectedAbstractions = connectionByConnectionName[connectionName]
        print(connectionName + " -" + (" " + RF.getStringRepresentationFromAbstraction(connection) if connection != None else "") + (" inv(" + RF.getStringRepresentationFromAbstraction(inverseConnection) + ")" if inverseConnection != None else ""))
        # Sort the connected abstractions by connected abstraction name
        connectedAbstractionNames = list(connectedAbstractions.keys())
        connectedAbstractionNames.sort(key = lambda x: (x[1].upper(), x[1]))
        # Print the connected abstractions
        for connectedAbstractionName in connectedAbstractionNames:
            print("    " + connectedAbstractionName + " - " + RF.getStringRepresentationFromAbstraction(connectedAbstractions[connectedAbstractionName]))

def runGetAbstractionGroup(abstraction, context):
    RF = context.get("RALFramework")
    # Get all abstract concepts, that are called by the same term
    isCalled = RalID(RF, "isCalled")
    search = RF.searchRALJPattern(triples = [(abstraction, isCalled, "term"), ("connectedAbstraction", isCalled, "term")])
    return set([x["connectedAbstraction"] for x in search]) | {abstraction}