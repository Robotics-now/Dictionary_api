import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException  # ← add this
from ai import correct_word
from lang import query_db, get_word_keys_for_lang
from config import DB_PATH, ALLOWED_LANGUAGES, CLIENT_DB_PATH, TEMPLATES_PATH, POS_JSON_PATH, API_ENDPOINT, API_PARTIAL_ENDPOINT, ERROR_MESSAGES
from client_serv import generate_key, submit_feedback, lookup_key, check_email
from json import load

app = FastAPI(docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory=TEMPLATES_PATH)
error_messages = ERROR_MESSAGES

def base_context(num: int=1 ,extra: dict = {} ) -> dict:
    if num == 1:
        context = {
            "api_endpoint": API_ENDPOINT}
    elif num == 2:
        context = {
            "api_endpoint": API_ENDPOINT,
            "api_partial_endpoint": API_PARTIAL_ENDPOINT
        }
    context.update(extra)
    
    return context

with open(POS_JSON_PATH, "r") as f:
    pos_dict = load(f)

def pos_name(pos_code: str) -> str:
    return pos_dict[pos_code] if pos_code in pos_dict else pos_code

# -- Pre-loading the English set for the spell-checker --
DICTIONARY_SET = get_word_keys_for_lang("eng")


#  ---Page routes---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html", context=base_context())

@app.get("/examples", response_class=HTMLResponse)
async def examples(request: Request):
    return templates.TemplateResponse(request=request, name="examples.html", context=base_context())

@app.get("/docs", response_class=HTMLResponse)
async def docs(request: Request):
    return templates.TemplateResponse(request=request, name="docs.html", context=base_context(2))

@app.get("/client", response_class=HTMLResponse)
async def client_page(request: Request):
    return templates.TemplateResponse(request=request, name="client.html", context=base_context())

@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html", context={})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request=request, name="about.html", context={})


#  ---Client routes (key generation + feedback)---
@app.post("/check-email")
async def handle_check_email(request: Request):
    return await check_email(request)

@app.post("/generate-key")                                 
async def handle_generate_key(request: Request):
    return await generate_key(request)

@app.post("/feedback")
async def handle_feedback(request: Request):
    return await submit_feedback(request)

@app.post("/lookup-key")
async def handle_lookup_key(request: Request):
    return await lookup_key(request)


#  ---API key validation helper---
def _validate_api_key(api_key: str) -> bool:
    """Return True if the key exists in client.db."""
    with sqlite3.connect(CLIENT_DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM keys WHERE api_key = ?",
            (api_key.strip(),)
        ).fetchone()
    return row is not None


#  ---Dictionary API route---
@app.get("/api/{api_key}/{language}/{word}")
async def get_definition(api_key: str, word: str, language: str = "eng"):

    try:
        
#  actual api logic
 
