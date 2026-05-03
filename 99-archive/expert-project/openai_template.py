import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

class Answer1(BaseModel):
    prompts: list[str]


# Load environment variables
load_dotenv()

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)

def ask_openai(system_prompt: str, user_message: str, response_format=None) -> str:
    """
    Sends a request to OpenAI API with both system prompt and user message.
    
    Args:
        system_prompt (str): The system prompt that defines AI behavior
        user_message (str): The actual user message or content to process
        
    Returns:
        str: The response from OpenAI
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    if response_format:
        response = openai_client.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=Answer1
        )
    else:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
    return response.choices[0].message.content.strip()