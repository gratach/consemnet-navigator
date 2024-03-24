from consemnet_navigator import *

import neo4j
import json

# Create a neo4j session

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"
DATABASE = "consemnet"
outputpath = "output.ralj"
with neo4j.GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
    session = driver.session(database=DATABASE)
    RF = neo4jRALFramework(session)
    context = {"RALFramework": RF}

    physics = RealWorldConcept(context, name="Physics")
    hasSubtopic = RealWorldConcept(context, connectionName="has specified subtopic", inverseConnectionName="is specified subtopic of")
    particlePhysics = RealWorldConcept(context, name="Particle Physics", baseConnections={(physics, hasSubtopic, 0)})

    input("Press enter to continue...")

    randomConcepts = []

    for i in range(100):
        randomConcepts.append(RealWorldConcept(context, name="Random Concept " + str(i)))

    input("Press enter to continue...")

    #runNavigator(context)

    saveRALJFile([*randomConcepts, physics, particlePhysics], outputpath, RF)

    input("Press enter to continue...")

    RF.close()
