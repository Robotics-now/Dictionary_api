from difflib import get_close_matches
from langchain_google_genai import ChatGoogleGenerativeAI
from os import getenv
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=getenv("GOOGLE_API_KEY"))

def correct_word(word: str, dictionary_words: set) -> str:
    normalized_word = word.lower().strip()
    
    # 1. Try fast local correction against the 175k set
    close_matches = get_close_matches(normalized_word, dictionary_words, n=1, cutoff=0.7)
    if close_matches:
        return close_matches[0]

    # 2. LLM Fallback
    try:
        response = llm.invoke(f"Correct this dictionary term to the single most likely intended dictionary word. Output only the word: {normalized_word}")
        return response.content.strip().lower()
    except Exception as e:
        print(f"LLM correction failed: {e}")
        return normalized_word
