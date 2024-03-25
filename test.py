from consemnet_navigator import *

import neo4j
import json

# Create a neo4j session

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"
DATABASE = "consemnet"
outputpath = "output.ralj"
SRF = SQLiteRALFramework("database.sqlite")
dda1 = SRF.DirectDataAbstraction("Physics", "text")
dda2 = SRF.DirectDataAbstraction("Particle Physics", "text")
ca1 = SRF.ConstructedAbstraction({(0, dda1, 0), (0, dda2, 0)})
if False:
    with neo4j.GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
        session = driver.session(database=DATABASE)
        RF = Neo4jRALFramework(session)
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
