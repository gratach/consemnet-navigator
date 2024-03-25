import sqlite3
from weakref import WeakValueDictionary

class SQLiteRALFramework:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._cur = self.conn.cursor()
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
        self.conn.commit()
    def DirectDataAbstraction(self, datastring, formatstring):
        # Check if the abstraction already exists
        self._cur.execute("SELECT id FROM abstractions WHERE data = ? AND format = ?", (datastring, formatstring))
        res = self._cur.fetchone()
        if res != None:
            return self._getAbstractionWrapperFromID(res[0])
        # Create the abstraction
        self._cur.execute("INSERT INTO abstractions (data, format, connections, remember) VALUES (?, ?, ?, ?)", (datastring, formatstring, None, 0))
        self.conn.commit()
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
        self._framework = framework
    @property
    def id(self):
        if self._id == None:
            raise ValueError("The abstraction has been deleted.")
        return self._id