from fastapi import APIRouter
from backend.api.tree_structure_api import router as structure_router
from backend.api.parser_api import router as parser_router
from backend.api.docgen_api import do_gen_router
router = APIRouter()

#Include Parser Router
router.include_router(parser_router)
#Include DocGen Router
router.include_router(do_gen_router)
# Include Structure Router
router.include_router(structure_router)