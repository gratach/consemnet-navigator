# Load and save data from RALJ files into the neo4j database.
# RALJ format documentation:
#   https://github.com/gratach/thoughts/blob/master/topics/data/graph/reduced-abstraction-layer-json.md

import json

def load_ralj_file(file_path, neo4j_session):
    with open(file_path, "r") as file:
        data = json.load(file)
    return load_ralj_data(data, neo4j_session)

def load_ralj_data(data, neo4j_session):
    assert type(data) == list and len(data) == 2
    dataConceptBlock = data[0]
    constructedConceptBlock = data[1]