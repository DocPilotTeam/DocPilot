from fastapi import FastAPI
from backend.db.data import user_repo_db
from backend.api.webhook import router as web_hook
from backend.api.api_routes import router as parser_api_router
from backend.agents.kg_builder.openAiKG import router as cypher_test
from backend.agents.watcher.CodeWatcher import router as watch_router
from backend.agents.kg_builder.Kg_reader import router as test_router
from backend.api.api_routes import do_gen_router as documentation_endpoint
from backend.agents.cloner.clone_agent import app as clone_agent_app   

app=FastAPI()

##CLONING AGENT
app.include_router(clone_agent_app.router,prefix="/api")
##CODE WATCHER
app.include_router(watch_router,prefix="/api")

##WebHook
app.include_router(web_hook,prefix="/api")

##CODE PARSER
app.include_router(parser_api_router, prefix="/api")

##Cypher Test Router
app.include_router(cypher_test,prefix="/api")

app.include_router(test_router,prefix="/api")

#DocGen Router
app.include_router(documentation_endpoint,prefix="/api")



app.include_router(authentication_router)

app.include_router(repositories_router,prefix="/api")