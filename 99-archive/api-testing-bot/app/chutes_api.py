import aiohttp
import asyncio
import json


async def invoke_chute(prompt: str, api_token: str, model: str = "Qwen/Qwen3-32B", max_tokens: int = 1024, temperature: float = 0.7):
	"""
	Invoke Chutes API to get LLM response
	
	Args:
		prompt: User message to send to the model
		api_token: API token for authentication
		model: Model name (default: Qwen/Qwen3-32B)
		max_tokens: Maximum tokens in response (default: 1024)
		temperature: Temperature for generation (default: 0.7)
	
	Returns:
		str: Complete response from the model
	"""
	headers = {
		"Authorization": "Bearer " + api_token,
		"Content-Type": "application/json"
	}
	
	body = {
		"model": model,
		"messages": [
			{
				"role": "user",
				"content": prompt
			}
		],
		"stream": True,
		"max_tokens": max_tokens,
		"temperature": temperature
	}

	response_text = ""
	
	async with aiohttp.ClientSession() as session:
		async with session.post(
			"https://llm.chutes.ai/v1/chat/completions", 
			headers=headers,
			json=body
		) as response:
			async for line in response.content:
				line = line.decode("utf-8").strip()
				if line.startswith("data: "):
					data = line[6:]
					if data == "[DONE]":
						break
					try:
						chunk = data.strip()
						if chunk:
							response_text += chunk
					except Exception as e:
						print(f"Error parsing chunk: {e}")
	
	return response_text


if __name__ == "__main__":
	# Test the function
	api_token = "$CHUTES_API_TOKEN"  # Replace with your actual API token
	asyncio.run(invoke_chute("Tell me a 250 word story.", api_token))
