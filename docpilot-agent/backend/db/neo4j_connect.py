from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("NEO4J_URL")
password = os.getenv("NEO4J_PASS")

print("Neo4j URI:", uri)

if not uri or not password:
    raise ValueError("Missing variables")

driver = GraphDatabase.driver(uri, auth=("neo4j", password))

try:
    driver.verify_connectivity()
    print("Connection established")
except Exception as e:
    print("Connection failed:", e)
