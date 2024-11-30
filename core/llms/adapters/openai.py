# llms/openai.py
from .base import BaseLLM, APIResponse
from django.conf import settings
from core.models import LLMModel
import requests
from typing import List
import json

class OpenAI(BaseLLM):
    def __init__(self, model: LLMModel):
        self._api_key = settings.OPENAI_API_KEY
        self.model = model

    def capabilities(self) -> List[str]:
        return self.model.capabilities
    
    def name(self) -> str:
        return self.model.model_name

    def query(self, query: dict) -> dict:
        query["model"] = self.model.model_name

        headers = {
            'Content-Type': 'application/json',
            'cf-aig-authorization': f"Bearer {settings.CLOUDFLARE_GATEWAY_AUTH_TOKEN}"
        }
        data = [
            {
                "provider": "openai",
                "endpoint": "chat/completions",
                "headers": {
                    "authorization": f"Bearer {self._api_key}",
                    "content-type": "application/json"
                },
                "query": query
            }
        ]
        
        # First attempt
        response = requests.post(
            self.GATEWAY_URL,
            headers=headers,
            json=data
        )
        
        # Retry once if we get a 500 error
        if response.status_code == 500:
            response = requests.post(
                self.GATEWAY_URL,
                headers=headers,
                json=data
            )
            
            # If still failing after retry, raise exception with error details
            if response.status_code != 200:
                error_message = response.json()
                raise Exception(f"OpenAI API request failed after retry: {error_message}")
        
        return response.json()

    def process_response(self, response: dict) -> str | dict:
        """
        Process the LLM API response and return either a string or structured data
        depending on the response format
        """
        content = response["choices"][0]["message"]["content"]
        
        # If response was requested in JSON format, parse it
        if "response_format" in response.get("usage", {}).get("system_tags", []):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback to returning raw content if JSON parsing fails
                return content
                
        return content