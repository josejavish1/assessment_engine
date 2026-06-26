import asyncio
import os

from google import genai
from google.genai import types


async def test_native_search():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="¿Quién ganó la Eurocopa 2024? Dime de qué fuente lo has sacado.",
        config=types.GenerateContentConfig(tools=[{"google_search": {}}]),
    )
    print("RESULTADO:", response.text)


if __name__ == "__main__":
    asyncio.run(test_native_search())
