from db.neo4j_connect import driver

def getFile(project):
    with driver.session() as session:
        result=session.run(
            "MATCH (f:File{project:$project}) return f"
        )

        return [record["f"] for record in result]
    