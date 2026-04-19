from difflib import get_close_matches
from langchain_google_genai import ChatGoogleGenerativeAI
import os
# Initialize LLM once
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=os.environ.get("GOOGLE_API_KEY"))

def correct_word(word: str, dictionary_words: set) -> str:
    normalized_word = word.lower().strip()
    
    # 1. Try fast local correction
    close_matches = get_close_matches(normalized_word, dictionary_words, n=1, cutoff=0.7)
    if close_matches:
        return close_matches[0]

    # 2. If local fails, use LangChain (The "Orange Path" in your drawing)
    try:
        response = llm.invoke(f"Correct this dictionary term to one word: {normalized_word}")
        return response.content.strip().lower()
    except:
        return normalized_word
