from consemnet_navigator import *

import neo4j

# Create a neo4j session

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"
DATABASE = "consemnet"
session = neo4j.GraphDatabase.driver(URI, auth=(USER, PASSWORD)).session(database=DATABASE)

# Create some abstractions
dda1 = DirectDataAbstraction("data1", "format1", session)
dda2 = DirectDataAbstraction("data2", "format1", session)

ca1 = ConstructedAbstraction([(None, dda1, dda2)], session)

deleteAbstraction(ca1, session)
deleteAbstraction(dda1, session)
deleteAbstraction(dda2, session)