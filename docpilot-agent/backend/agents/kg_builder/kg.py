from db.neo4j_connect import driver

def addFileNode(file_path):
    query = """
    MERGE (f:File {path: $path})
    RETURN f
    """

    with driver.session() as session:
        session.run(query=query,path=file_path)


def addClassNode(class_name,file_path):
    query="""
    MATCH(f:File{path:$file_path})
    MERGE(c:ClassName{name:$class_name})
    MERGE(f)-[:contains]->(c)
    RETURN c
    """
    with driver.session() as session:
        session.run(query=query,class_name=class_name,file_path=file_path)

def addMethodNode(method_name,target_name):
    query="""
    MATCH(m1:Method{name:$method_name})
    
    """

