import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Fallback to config value
    from app.config import get_settings
    api_key = get_settings().gemini_api_key

genai.configure(api_key=api_key)

print("Listing available embedding models:")
try:
    for m in genai.list_models():
        if "embedContent" in m.supported_generation_methods:
            print(f"- {m.name} (displayName: {m.display_name})")
except Exception as e:
    print("Error listing models:", e)
