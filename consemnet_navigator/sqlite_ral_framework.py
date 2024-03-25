import sqlite3
from weakref import WeakValueDictionary

class SQLiteRALFramework:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._cur = self._conn.cursor()
        self._cur.execute("CREATE TABLE IF NOT EXISTS abstractions (id INTEGER PRIMARY KEY, data TEXT, format TEXT, connections TEXT, tripleIds TEXT, remember INTEGER)")
        self._cur.execute("CREATE TABLE IF NOT EXISTS triples (id INTEGER PRIMARY KEY, subject INTEGER, predicate INTEGER, object INTEGER, owner INTEGER)")
        self._wrappersByAbstractionID = WeakValueDictionary()
    def ConstructedAbstraction(self, baseConnections):
        # Iterate through the base connections and create the triple representations
        tripleRepresentations = []
        for triple in baseConnections:
            if not 0 in triple or len(triple) != 3:
                raise ValueError("The base connections must consist of triples with at least one element being 0.")
            if triple[0] == 0:
                subject = "-"
            elif type(triple[0]) == SQLiteAbstraction:
                subject = str(triple[0].id)
            else:
                raise ValueError("The subject of a triple must be an abstraction.")
            if triple[1] == 0:
                predicate = "-"
            elif type(triple[1]) == SQLiteAbstraction:
                predicate = str(triple[1].id)
            else:
                raise ValueError("The predicate of a triple must be an abstraction.")
            if triple[2] == 0:
                object = "-"
            elif type(triple[2]) == SQLiteAbstraction:
                object = str(triple[2].id)
            else:
                raise ValueError("The object of a triple must be an abstraction.")
            tripleRepresentations.append((subject, predicate, object))
        tripleRepresentations.sort()
        connectionRepresentationString = "|".join([",".join(triple) for triple in tripleRepresentations])
        # Check if the abstraction already exists
        self._cur.execute("SELECT id FROM abstractions WHERE connections = ?", (connectionRepresentationString,))
        res = self._cur.fetchone()
        if res != None:
            return self._getAbstractionWrapperFromID(res[0])
        # Create the abstraction
        self._cur.execute("INSERT INTO abstractions (data, format, connections, tripleIds, remember) VALUES (?, ?, ?, ?, ?)", (None, None, connectionRepresentationString, None, 0))
        result = self._getAbstractionWrapperFromID(self._cur.lastrowid)
        # Create the triples
        tripleIds = []
        for triple in baseConnections:
            self._cur.execute("INSERT INTO triples (subject, predicate, object, owner) VALUES (?, ?, ?, ?)", (triple[0].id if triple[0] != 0 else result.id, triple[1].id if triple[1] != 0 else result.id, triple[2].id if triple[2] != 0 else result.id, result.id))
            tripleIds.append(self._cur.lastrowid)
        tripleIdRepresentationString = ",".join([str(tripleId) for tripleId in tripleIds])
        self._cur.execute("UPDATE abstractions SET tripleIds = ? WHERE id = ?", (tripleIdRepresentationString, result.id))
        self._conn.commit()
        return result
    def DirectDataAbstraction(self, datastring, formatstring):
        # Check if the abstraction already exists
        self._cur.execute("SELECT id FROM abstractions WHERE data = ? AND format = ?", (datastring, formatstring))
        res = self._cur.fetchone()
        if res != None:
            return self._getAbstractionWrapperFromID(res[0])
        # Create the abstraction
        self._cur.execute("INSERT INTO abstractions (data, format, connections, remember) VALUES (?, ?, ?, ?)", (datastring, formatstring, None, 0))
        self._conn.commit()
        return self._getAbstractionWrapperFromID(self._cur.lastrowid)
    def _getAbstractionWrapperFromID(self, id):
        if id in self._wrappersByAbstractionID:
            return self._wrappersByAbstractionID[id]
        wrapper = SQLiteAbstraction(id, self)
        self._wrappersByAbstractionID[id] = wrapper
        return wrapper
    def close(self):
        for wrapper in self._wrappersByAbstractionID.values():
            wrapper._safeDelete()
        self._conn.close()
    def isValidAbstraction(self, abstraction):
        return type(abstraction) == SQLiteAbstraction and abstraction.RALFramework == self and abstraction._id != None
    def searchRALJPattern(self, data = {}, constructed = {}, triples = []):
        # Create the search modules
        dataBlock, constructedBlock, tripleBlock = data, constructed, triples
        knownParameters = {}
        searchModules = []
        for dataParam, (data, format) in dataBlock.items():
            if type(data) == str and type(format) == str:
                knownParameters[dataParam] = self.DirectDataAbstraction(data, format).id
            else:
                searchModules.append(DataSearchModule(dataParam, data, format))
        for constructedParam, baseConnections in constructedBlock.items():
            exactNumberOfBaseConnections = True
            if len(baseConnections) > 0 and baseConnections[-1] == "+":
                baseConnections = baseConnections[:-1]
                exactNumberOfBaseConnections = False
            for i in range(len(baseConnections)):
                searchModules.append(ConstructedSearchModule(constructedParam, baseConnections, i, exactNumberOfBaseConnections, self))
        for subj, pred, obj in tripleBlock:
            searchModules.append(TripleSearchModule(subj, pred, obj, self))
        # Search for all possible parameter combinations
        for knownParameters in searchAllSearchModules(searchModules, knownParameters):
            # Replace all id parameters with the corresponding abstractions
            yield {key : (self._getAbstractionWrapperFromID(value) if type(value) == int else value) for key, value in knownParameters.items()}
    def getStringRepresentationFromAbstraction(self, abstraction):
        if type(abstraction) != SQLiteAbstraction:
            raise ValueError("The abstraction must be a SQLiteAbstraction.")
        return str(abstraction.id)
    def getAbstractionFromStringRepresentation(self, stringRepresentation):
        self._cur.execute("SELECT id FROM abstractions WHERE id = ?", (int(stringRepresentation),))
        res = self._cur.fetchone()
        if res == None:
            raise ValueError("The abstraction with the given id does not exist.")
        return self._getAbstractionWrapperFromID(res[0])

class ConstructedSearchModule:
    def __init__(self, param, baseConnections, connectionIndex, exactNumberOfBaseConnections, framework):
        self.framework = framework
        self.param = param
        self.baseConnections = baseConnections
        self.connectionIndex = connectionIndex
        self.exactNumberOfBaseConnections = exactNumberOfBaseConnections
        self.subj = baseConnections[connectionIndex][0]
        self.pred = baseConnections[connectionIndex][1]
        self.obj = baseConnections[connectionIndex][2]
        self.subj = self.subj if type(self.subj) != 0 else param
        self.pred = self.pred if type(self.pred) != 0 else param
        self.obj = self.obj if type(self.obj) != 0 else param
        self.parameterNames = {param} if type(param) == str else {} | {self.subj} if type(self.subj) == str else set() | {self.pred} if type(self.pred) == str else set() | {self.obj} if type(self.obj) == str else set()
    def search(self, knownParameters):
        subjValue = self.subj.id if type(self.subj) == SQLiteAbstraction else knownParameters.get(self.subj, None)
        predValue = self.pred.id if type(self.pred) == SQLiteAbstraction else knownParameters.get(self.pred, None)
        objValue = self.obj.id if type(self.obj) == SQLiteAbstraction else knownParameters.get(self.obj, None)
        ownerValue = self.param.id if type(self.param) == SQLiteAbstraction else knownParameters.get(self.param, None)
        self.framework._cur.execute("SELECT subject, predicate, object, owner FROM triples WHERE " +
                                    " AND ".join([
                                        *(["subject = ?"] if subjValue != None else []), 
                                        *(["predicate = ?"] if predValue != None else []), 
                                        *(["object = ?"] if objValue != None else []), 
                                        *(["owner = ?"] if ownerValue != None else [])]),
                                    tuple([
                                        *([subjValue] if subjValue != None else []), 
                                        *([predValue] if predValue != None else []), 
                                        *([objValue] if objValue != None else []), 
                                        *([ownerValue] if ownerValue != None else [])]))
        matchingTriples = self.framework._cur.fetchall()
        if len(matchingTriples) == 0:
            return
        # Create the set of already matched triples
        alreadyMatchedTriples = set()
        for i, matchingTriple in enumerate(self.baseConnections):
            if i != self.connectionIndex:
                subjValue = matchingTriple[0].id if type(matchingTriple[0]) == SQLiteAbstraction else knownParameters.get(matchingTriple[0], None)
                predValue = matchingTriple[1].id if type(matchingTriple[1]) == SQLiteAbstraction else knownParameters.get(matchingTriple[1], None)
                objValue = matchingTriple[2].id if type(matchingTriple[2]) == SQLiteAbstraction else knownParameters.get(matchingTriple[2], None)
                if not None in [subjValue, predValue, objValue]:
                    alreadyMatchedTriples.add((subjValue, predValue, objValue))
        # Iterate through the matching triples
        for matchingTriple in matchingTriples:
            # If the owner got a new value, check if there is an exact number of base connections
            if ownerValue == None and self.exactNumberOfBaseConnections:
                self.framework._cur.execute("SELECT COUNT(*) FROM triples WHERE owner = ?", (matchingTriple[3],))
                if self.framework._cur.fetchone()[0] != len(self.baseConnections):
                    continue
            # Check if the triple is already matched
            if (matchingTriple[0], matchingTriple[1], matchingTriple[2]) in alreadyMatchedTriples:
                continue
            yield {**({self.subj : matchingTriple[0]} if type(self.subj) == str else {}),
                   **({self.pred : matchingTriple[1]} if type(self.pred) == str else {}),
                   **({self.obj : matchingTriple[2]} if type(self.obj) == str else {}),
                   **({self.param : matchingTriple[3]} if type(self.param) == str else {})}

class TripleSearchModule:
    def __init__(self, subj, pred, obj, framework):
        self.subj = subj
        self.pred = pred
        self.obj = obj
        self.framework = framework
        self.parameterNames = {subj} if type(subj) == str else set() | {pred} if type(pred) == str else set() | {obj} if type(obj) == str else set()
    def search(self, knownParameters):
        subjValue = self.subj.id if type(self.subj) == SQLiteAbstraction else knownParameters.get(self.subj, None)
        predValue = self.pred.id if type(self.pred) == SQLiteAbstraction else knownParameters.get(self.pred, None)
        objValue = self.obj.id if type(self.obj) == SQLiteAbstraction else knownParameters.get(self.obj, None)
        self.framework._cur.execute("SELECT subject, predicate, object FROM triples WHERE " + 
                                                        " AND ".join([
                                                            *(["subject = ?"] if subjValue != None else []), 
                                                            *(["predicate = ?"] if predValue != None else []), 
                                                            *(["object = ?"] if objValue != None else [])]), 
                                                        tuple([
                                                            *([subjValue] if subjValue != None else []), 
                                                            *([predValue] if predValue != None else []), 
                                                            *([objValue] if objValue != None else [])]))
        matchingTriples = self.framework._cur.fetchall()
        for matchingTriple in matchingTriples:
            yield {**({self.subj : matchingTriple[0]} if type(self.subj) == str else {}),
                   **({self.pred : matchingTriple[1]} if type(self.pred) == str else {}),
                   **({self.obj : matchingTriple[2]} if type(self.obj) == str else {})}
                
        
                                   
def searchAllSearchModules(searchModules, knownParameters):
    """
    Return all filled parameter combinations for the given modules.
    """
    # If there are no modules yield the known parameters
    if len(searchModules) == 0:
        yield knownParameters
        return
    # Get the module with the smallest number of unknown parameters
    smallestNumberOfUnknownParameters = 100000000000
    moduleWithSmallestNumberOfUnknownParameters = None
    for searchModule in searchModules:
        moduleParameters = searchModule.parameterNames
        numberOfUnknownParameters = len([parameter for parameter in moduleParameters if parameter not in knownParameters])
        if numberOfUnknownParameters < smallestNumberOfUnknownParameters:
            smallestNumberOfUnknownParameters = numberOfUnknownParameters
            moduleWithSmallestNumberOfUnknownParameters = searchModule
    # Iterate through all possible values for the unknown parameters of the module
    for parameterValues in moduleWithSmallestNumberOfUnknownParameters.search(knownParameters):
        # Add the parameter values to the known parameters
        newKnownParameters = knownParameters | parameterValues
        # Recursively search for the remaining modules
        for newKnownParameters in searchAllSearchModules([searchModule for searchModule in searchModules if searchModule != moduleWithSmallestNumberOfUnknownParameters], newKnownParameters):
            yield newKnownParameters


class SQLiteAbstraction:
    def __init__(self, abstractionId, framework):
        self._id = abstractionId
        self.RALFramework = framework
    @property
    def id(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return self._id
    @property
    def data(self):
        self.RALFramework._cur.execute("SELECT data FROM abstractions WHERE id = ?", (self.id,))
        return self.RALFramework._cur.fetchone()[0]
    @property
    def format(self):
        self.RALFramework._cur.execute("SELECT format FROM abstractions WHERE id = ?", (self.id,))
        return self.RALFramework._cur.fetchone()[0]
    @property
    def connections(self):
        self.RALFramework._cur.execute("SELECT connections FROM abstractions WHERE id = ?", (self.id,))
        triples = self.RALFramework._cur.fetchone()[0].split("|")
        triples = [tuple([0 if element == "-" else self.RALFramework._getAbstractionWrapperFromID(int(element)) for element in triple.split(",")]) for triple in triples]
        return frozenset(triples)
    @property
    def remembered(self):
        self.RALFramework._cur.execute("SELECT remember FROM abstractions WHERE id = ?", (self.id,))
        return self.RALFramework._cur.fetchone()[0] != 0
    @property
    def type(self):
        self.RALFramework._cur.execute("SELECT data FROM abstractions WHERE id = ?", (self.id,))
        return "DirectDataAbstraction" if self.RALFramework._cur.fetchone()[0] != None else "ConstructedAbstraction"
    def __repr__(self):
        if self._id == None:
            return f"Abstraction(deleted)"
        return f"Abstraction({self.id})"
    def __del__(self):
        self._safeDelete()
    def _safeDelete(self):
        if self._id == None:
            return
        id = self.id
        self._id = None
        # Check if the abstraction can be savely deleted from the sqlite database
        idsToCheckForDeletion = set([id])
        while len(idsToCheckForDeletion) > 0:
            id = idsToCheckForDeletion.pop()
            idsToCheckForDeletion |= checkForSafeAbstractionDeletion(id, self.RALFramework)

def checkForSafeAbstractionDeletion(id, RALFramework):
    """
    Checks if the abstraction with the given id can be savely deleted from the sqlite database.
    Returns a set of the abstraction ids that should also be checked for safe deletion.
    """
    # Check if the abstraction is remembered
    if RALFramework._cur.execute("SELECT remember FROM abstractions WHERE id = ?", (id,)).fetchone()[0] != 0:
        return set()
    # Check if tere is a active wrapper for the abstraction
    wrapper = RALFramework._wrappersByAbstractionID.get(id)
    if wrapper != None and wrapper._id != None:
        return set()
    # Get all the connected Triples
    triples = RALFramework._cur.execute("SELECT id, subject, predicate, object, owner FROM triples WHERE subject = ? OR predicate = ? OR object = ?", (id, id, id)).fetchall()
    # Check if all triples are owned by the abstraction
    for triple in triples:
        if triple[4] != id:
            return set()
    # Collect all connected abstractions
    connectedAbstractions = set()
    for triple in triples:
        for element in triple[1:4]:
            if element != id:
                connectedAbstractions.add(element)
    # Delete the triples
    for triple in triples:
        RALFramework._cur.execute("DELETE FROM triples WHERE id = ?", (triple[0],))
    # Delete the abstraction
    RALFramework._cur.execute("DELETE FROM abstractions WHERE id = ?", (id,))
    RALFramework._conn.commit()
    # Return the connected abstractions
    return connectedAbstractions
    