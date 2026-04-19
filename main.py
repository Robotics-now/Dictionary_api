import pandas as pd
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ai import correct_word

app = FastAPI(docs_url="/docs", redoc_url=None, openapi_url="/openapi.json") # Custom docs path
templates = Jinja2Templates(directory="templates")

# Load your database
df = pd.read_csv('dictionary.csv')

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="home.html", 
        context={} 
    )

@app.get("/examples", response_class=HTMLResponse)
async def examples(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="examples.html", 
        context={} 
    )

@app.get("/api/{word}")
async def get_definition(word: str):
    query_word = word.lower().strip()
    
    # 2. Check Database
    result = df.loc[df['word'] == query_word]
    
    if not result.empty:
        definition = result["definition"].squeeze()
        return {
            "word": query_word,
            "def": definition,
            "thesaurus": "Coming soon...",
        }
    
    # 3. Word not found in dictionary -> use correction logic
    corrected_word = correct_word(query_word)
    corrected_result = df.loc[df['word'] == corrected_word]

    if not corrected_result.empty:
        definition = corrected_result["definition"].squeeze()
        return {
            "word": corrected_word,
            "def": definition,
            "thesaurus": "Coming soon...",
            "original_word": query_word,
        }

    # 4. No dictionary match after correction
    return {
        "word": corrected_word,
        "def": None,
        "thesaurus": "Coming soon...",
        "original_word": query_word,
    }
