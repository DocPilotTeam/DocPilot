from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

uri=os.getenv("neo4j_url")
password=os.getenv("neo4j_pass")
AUTH=("neo4j",password)
print(uri)
print(password)

## verify connection

if not uri or not password:
    raise ValueError("Missing variables")

driver=GraphDatabase.driver(uri,auth=("neo4j",password))

with driver:
    driver.verify_connectivity()
    print("Connection established")
