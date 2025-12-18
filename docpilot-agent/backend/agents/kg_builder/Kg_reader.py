from backend.db.neo4j_connect import driver
from fastapi import APIRouter

router=APIRouter()


def getFile(project):
    with driver.session() as session:
        result=session.run(
            "MATCH (f:File{project:$project}) return f",
            project=project
        )

        return [record["f"] for record in result]

def getClasses(project, file_path):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Class {filePath: $file, project: $project})
            RETURN c
            """,
            file=file_path,
            project=project
        )
        return [record["c"] for record in result]

    
def getMethods(project, class_name):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (m:Method {parentClass: $class_name, project: $project})
            RETURN m
            """,
            class_name=class_name,
            project=project
        )
        return [record["m"] for record in result]


def get_method_calls(project, class_name, method_name):
    with driver.session() as session:
        query = """
        MATCH (m:Method {name: $method, parentClass: $parentClass, project: $project})
        MATCH (m)-[:CALLS]->(target:Method)
        RETURN target
        """

        result = session.run(
            query,
            method=method_name,
            parentClass=class_name,  
            project=project
        )

        return [record["target"] for record in result]
    

@router.get("/testingDataRetrive")
def dataRetrive(projectName: str):

    data = []

    files = getFile(projectName)
    data.extend(files)

    for f in files:
        file_path = f["filePath"]

        classes = getClasses(projectName, file_path)
        data.extend(classes)

        for c in classes:
            class_name = c["name"]

            methods = getMethods(projectName, class_name)
            data.extend(methods)

            # Will be empty until CALLS relationships exist
            for m in methods:
                method_calls = get_method_calls(
                    projectName,
                    class_name,
                    m["name"]
                )
                data.extend(method_calls)

    return data


    # print("Classes:", getClasses(projectName, file_path))
    # print("Methods:", getMethods(projectName, class_name))
    # print("Method calls:", get_method_calls(projectName, class_name, method_name))

    data=[]

      
    files = getFile(projectName)
    data.extend(files)

    
    for f in files:
        file_path = f["filePath"]
        classes = getClasses(projectName, file_path)
        print(classes)
        data.extend(classes)

        
        for c in classes:
            class_name = c["name"]
            methods = getMethods(projectName, class_name)
            print(methods)
            data.extend(methods)

            
            for m in methods:
                method_name = m["name"]
                method_calls = get_method_calls(projectName, class_name, method_name)
                print(method_calls)
                data.extend(method_calls)
                
    return data

    