from .network_tools import getIndirectConnections

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
    baseConnections = RF.getBaseConnections(currentAbstraction)
    # Print the base connections
    print("Base connections: [")
    for connection in baseConnections:
        print("    " + ", ".join([" - " if x == None else getAbstractionName(x, context.get("getAbstractionNameContext", context)) for x in connection]) + ",")
    print("]")
    # Get the indirect connections of the current abstraction
    indirectConnections = getIndirectConnections(currentAbstraction, RF)
    # Print the indirect connections
    print("Indirect connections: [")
    for connection in indirectConnections:
        print("    " + ", ".join([" - " if x == None else getAbstractionName(x, context.get("getAbstractionNameContext", context)) for x in connection]) + ",")
    print("]")

def runNavigatorInput(context):
    # Get the input
    input = input("Enter the abstraction index or a command: ")
    # Check if the input is a command
    if input == "exit":
        context["navigatorExit"] = True
    # Check if the input is a number
    elif input.isdigit():
        # Get the abstraction index
        abstractionIndex = int(input)
        # Set the current abstraction
        context["currentAbstraction"] = abstractionIndex

def getCurrentAbstraction(context):
    # Get a list of all abstractions