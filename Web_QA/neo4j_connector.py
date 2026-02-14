from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jConnector:
    def __init__(self):
        self._uri = os.getenv("NEO4J_URI")
        self._user = os.getenv("NEO4J_USER")
        self._password = os.getenv("NEO4J_PASSWORD")
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))

    def close(self):
        self._driver.close()

    def execute_query(self, query, parameters=None):
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]