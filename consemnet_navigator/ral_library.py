from pathlib import Path
import sqlite3
from random import randint
from tempfile import NamedTemporaryFile
from .ralj_loader import loadRALJFile, loadRALJData, saveRALJFile, saveRALJData
from .sqlite_ral_framework import SQLiteRALFramework
from .network_transformation import transformRALNetwork, RALIdentityTransformation

readmeText = """
# RAL Library
"""

class RALLibrary:
    def __init__(self, path, keywordFinder = None):
        """
        A library of RAL data, that is stored internally in different ralj files.
        The RALLibrary keeps track which of those files contain which keywords of which indices.
        """
        if keywordFinder == None:
            keywordFinder = findTextKeywords
        self._keywordFinder = keywordFinder
        self._path = Path(path).resolve()
        self._rootPath = self._path.parent
        assert self._rootPath.is_dir()
        self._path.mkdir(exist_ok=True)
        self._dataPath = self._path / "data"
        self._dataPath.mkdir(exist_ok=True)
        self._readmePath = self._path / "README.md"
        if not self._readmePath.exists():
            self._readmePath.write_text(readmeText)
        self._indexPath = self._path / "index.sqlite"
        self._conn = sqlite3.connect(str(self._indexPath))
        self._cur = self._conn.cursor()
        self._cur.execute("CREATE TABLE IF NOT EXISTS dataFiles (id INTEGER PRIMARY KEY, name TEXT)")
        self._cur.execute("CREATE TABLE IF NOT EXISTS keywords (id INTEGER PRIMARY KEY, keyword INTEGER, UNIQUE(keyword))")
        self._cur.execute("CREATE TABLE IF NOT EXISTS keywordOccurrences (keywordId INTEGER, dataFileId INTEGER)")
        self._conn.commit()
    def saveData(self, abstractConcepts, RALFramework):
        """
        Save the data to the library and return the set of keywords.
        """
        with NamedTemporaryFile() as tempFile:
            with SQLiteRALFramework(tempFile.name) as SRF:
                result = transformRALNetwork(abstractConcepts, RALFramework, SRF, RALIdentityTransformation)
                keywords = self._keywordFinder(SRF)
        hexname = self._saveDataToFile(abstractConcepts, RALFramework)
        self._addFileToIndex(hexname, keywords)
    def loadData(self, keywords, RALFramework):
        """
        Load the data that is associated with a single keyword or a set of keywords.
        """
        keywords = keywords if type(keywords) in (list, set, tuple) else [keywords]
        relevantFiles = set()
        for keyword in keywords:
            self._cur.execute("SELECT name FROM dataFiles WHERE id IN (SELECT dataFileId FROM keywordOccurrences WHERE keywordId IN (SELECT id FROM keywords WHERE keyword = ?))", (keyword,))
            relevantFiles.update([x[0] for x in self._cur.fetchall()])
        result = set()
        for hexname in relevantFiles:
            result.update(self._loadDataFromFile(hexname, RALFramework).values())
        return result
    def _addFileToIndex(self, hexname, keywords):
        self._cur.execute("INSERT INTO dataFiles (name) VALUES (?)", (hexname,))
        dataFileId = self._cur.lastrowid
        for keyword in keywords:
            self._cur.execute("INSERT OR IGNORE INTO keywords (keyword) VALUES (?)", (keyword,))
            keywordId = self._cur.lastrowid
            self._cur.execute("INSERT INTO keywordOccurrences (keywordId, dataFileId) VALUES (?, ?)", (keywordId, dataFileId))
        self._conn.commit()
    def _saveDataToFile(self, abstractConcepts, RALFramework):
        hexname = ""
        dataFilePath = None
        while True:
            hexname += bytes([randint(0, 255)]).hex()
            dataFilePath = self._dataPath / (hexname + ".ralj")
            if not dataFilePath.exists():
                break
        saveRALJFile(abstractConcepts, str(dataFilePath), RALFramework)
        return hexname
    def _loadDataFromFile(self, hexname, RALFramework):
        dataFilePath = self._dataPath / (hexname + ".ralj")
        return loadRALJFile(str(dataFilePath), RALFramework)

def findTextKeywords(RALFramework):
    """
    Returns the content of all text direct data abstractions in the RALFramework.
    """
    result = RALFramework.searchRALJPattern(data = {"text" : (["data"], "text")})
    return [x["data"] for x in result]