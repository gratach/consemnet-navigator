from consemnet_navigator import *

import neo4j

# Create a neo4j session

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"
DATABASE = "consemnet"
with neo4j.GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
    session = driver.session(database=DATABASE)
    RF = neo4jRALFramework(session)

    # Create some abstractions
    dda1 = RF.DirectDataAbstraction("data1", "format1")
    dda2 = RF.DirectDataAbstraction("data2", "format1")

    da1 = RF.DirectAbstraction(dda1)

    ca1 = RF.ConstructedAbstraction([(None, da1, dda2)])
    ca2 = RF.ConstructedAbstraction([(None, dda1, ca1),
                                (None, None, dda2)])

    print(RF.getAbstractionContent(ca1))
    print(RF.getAbstractionContent(ca2))
    print(RF.getAbstractionType(ca1))
    print(RF.getAbstractionType(dda2))

    print(saveRALJData([ca2], RF))
    loaded = loadRALJData([
        {"string": {"hallo" : 1, "welt" : 2}},
        { 
            5 : [[0, 3, 1]],
            7 : [[0, 4, 6],
                 [0, 1, 1]]
        },
        {3 : 1, 6 : 5},
        {4 : 2}
    ], RF)

    print("loaded", loaded)

    searched = RF.searchRALJPattern([
        {"string": {"welt" : 2}},
        {7 : [[0, 4, 6], "+"],},
        {6 : [loaded[5]]},
        {4 : 2}
        ])
    
    print("searched", searched)

    searched2 = RF.searchRALJPattern([
        {"string": {"hallo" : 1}},
        {3 : [[0, 2, 1], "+"],},
        ])
    
    print("searched2", searched2)

    RF.deleteAbstraction(ca2)
    #deleteAbstraction(ca1, session)
    #deleteAbstraction(dda1, session)
    #deleteAbstraction(dda2, session)