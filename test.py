from consemnet_navigator import *

import neo4j
import json

# Create a neo4j session

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"
DATABASE = "consemnet"
with neo4j.GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
    session = driver.session(database=DATABASE)
    RF = neo4jRALFramework(session)

    physics = RealWorldConcept(RF, name="Physics")
    hasSubtopic = RealWorldConcept(RF, connectionName="has specified subtopic", inverseConnectionName="is specified subtopic of")
    particlePhysics = RealWorldConcept(RF, name="Particle Physics", baseConnections={(physics, hasSubtopic, 0)})

    input("Press enter to continue...")

    randomConcepts = set()
    for i in range(10):
        randomConcepts.add(RealWorldConcept(RF, name="Random Concept " + str(i)))
        
    input("Press enter to continue...")

    RF.close()