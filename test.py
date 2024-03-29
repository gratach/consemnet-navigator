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
SRF2 = SQLiteRALFramework("database2.sqlite")
SRF3 = SQLiteRALFramework("database3.sqlite")
RL = RALLibrary("ral_library")
"""
dda1 = SRF.DirectDataAbstraction("Physics", "text")
dda2 = SRF.DirectDataAbstraction("Particle Physics", "text")
exist = SRF.DirectDataAbstraction("exist", "claim")
print(dda1.data)
print(dda1.format)
print(dda1.type)
ca1 = SRF.ConstructedAbstraction({(0, 0, dda2), (0, exist, 0)})
ca2 = SRF.ConstructedAbstraction({(dda1, 0, ca1), (0, exist, 0)})
print(ca1.connections)
print(ca1.type)
ca1.remembered = True
#search = [*SRF.searchRALJPattern(triples = [["1", dda2, "1"], [dda1, "2", "1"]])]
#search = [*SRF.searchRALJPattern(constructed = {"2" : [[0, dda2, "1"], [dda1, "2", ca1]]})]
search = [*SRF.searchRALJPattern(data = {"dataconcept1" : (["data"], ["text"])}, constructed = {"constructedconcept1" : [["dataconcept1", 0, "someconcept"], "+"]})]
print(search)
transformresult1  = transformAssertedClaimsIntoAbstractClaims({dda1, dda2, ca1, ca2}, SRF, SRF2)
print(transformresult1)
transformresult2  = transformAbstractClaimsIntoAssertedClaims(transformresult1, SRF2, SRF3)
print(transformresult2)
"""
#with neo4j.GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
#session = driver.session(database=DATABASE)
#RF = Neo4jRALFramework(session)
context = {"RALFramework": SRF, "RALLibrary": RL}
tempStorageDict = context.setdefault("tempStorageDict", {})
hasSubtopic = RealWorldConcept(SRF, connectionName="has specified subtopic", inverseConnectionName="is specified subtopic of")
physics = RealWorldConcept(SRF, name="Physics")
particlePhysicsSubtopicOfPhysics = RealWorldConcept(SRF, name="Particle Physics", baseConnections={(physics, hasSubtopic, 0)})
science = RealWorldConcept(SRF, name="Science")
physicsSubtopicOfScience = RealWorldConcept(SRF, name="Physics", baseConnections={(science, hasSubtopic, 0)})
RL.saveData([physics, particlePhysicsSubtopicOfPhysics, science, physicsSubtopicOfScience], SRF)

input("Press Enter to continue...")
testRealworldConcepts = []
for i in range(0, 1000):
    testRealworldConcepts.append(RealWorldConcept(SRF, name="Test Realworld Concept " + str(i)))

input("Press Enter to continue...")

context["currentAbstraction"] = physics
context["displayEnvironment"] = runDisplayRealWorldConceptEnvironment

runNavigator(context)
    #RF.close()
