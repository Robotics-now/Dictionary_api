import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ai import correct_word

app = FastAPI(docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory="templates")

DB_PATH = "dictionary.db"
ALLOWED_LANGUAGES = ['eng']

def query_db(word: str, language: str):
    table_name = language.lower().strip()
    
    if table_name not in ALLOWED_LANGUAGES:
        return []
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                f"SELECT * FROM {table_name} WHERE TRIM(LOWER(word)) = ?",
                (word.lower().strip(),)
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
    return rows

def get_word_keys_for_lang(language: str):
    table_name = language.lower().strip()
    
    if table_name not in ALLOWED_LANGUAGES:
        return set()
    
    with sqlite3.connect(DB_PATH) as conn:
        try:
            words = {row[0] for row in conn.execute(f"SELECT word FROM {table_name}").fetchall()}
        except sqlite3.OperationalError:
            words = set()
    return words

# --Pre-loading the English set for the spell-checker--
# --Later, you can make this a dictionary: DICTIONARY_CACHE = {"english": {...}, "spanish": {...}}--
DICTIONARY_SET = get_word_keys_for_lang("eng")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html", context={})

@app.get("/examples", response_class=HTMLResponse)
async def examples(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="examples.html", 
        context={} 
    )

@app.get("/docs", response_class=HTMLResponse)
async def docs(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="docs.html", 
        context={} 
    )

@app.get("/api/{language}/{word}")
async def get_definition(word: str, language: str):

    if language.lower().strip() not in ALLOWED_LANGUAGES:
        return {"word": word, "results": [], "error": f"Language '{language}' is not supported."}
    
    query_word = word.lower().strip()
    target_lang = language.lower().strip()
    # --Search Database in the specific language table--
    rows = query_db(query_word, target_lang)
    
    # --If not found, try Correction (currently using English set as default)--
    if not rows:
        # If searching english, use the pre-loaded set; otherwise load on the fly
        current_set = get_word_keys_for_lang(target_lang)        
        corrected = correct_word(query_word, current_set)
        rows = query_db(corrected, target_lang)
        query_word = corrected

    # 3. Format results
    if rows:
        results_list = []
        for row in rows:
            # Handle column variations
            definition = row['definition'] if 'definition' in row.keys() else row['def']
            
            results_list.append({
                "definition": definition,
                "pos": row['pos'],
                "synonyms": row['synonyms'],
                "antonyms": row['antonyms']
            })
        
        return {
            "word": query_word,
            "results": results_list,
            "error": None
        }

    # 4. Final Fallback
    return {
        "word": word,
        "results": [],
        "error": f"Word not found in the {target_lang} dictionary."
    }
