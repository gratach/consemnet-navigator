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

    hasSubtopic = RealWorldConcept(context, connectionName="has specified subtopic", inverseConnectionName="is specified subtopic of")
    physics = RealWorldConcept(context, name="Physics")
    particlePhysicsSubtopicOfPhysics = RealWorldConcept(context, name="Particle Physics", baseConnections={(physics, hasSubtopic, 0)})
    science = RealWorldConcept(context, name="Science")
    physicsSubtopicOfScience = RealWorldConcept(context, name="Physics", baseConnections={(science, hasSubtopic, 0)})

    context["currentAbstraction"] = physics
    context["displayEnvironment"] = runDisplayRealWorldConceptEnvironment

    runNavigator(context)

    RF.close()
