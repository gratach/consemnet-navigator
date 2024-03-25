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
    