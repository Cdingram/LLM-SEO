from typing import List
from .base import BaseLLMTest, TestResult
from core.llms.adapters.base import BaseLLM
from pydantic import BaseModel

class SentimentAnalysisResponse(BaseModel):
    sentiment: str
    confidence: float
    explanation: str

class SentimentAnalysisTest(BaseLLMTest):
    required_capabilities = ["chat"]

    def __init__(self, text: str):
        self.text = text

    @classmethod
    def test_name(cls) -> str:
        return "sentiment_analysis"

    @property
    def description(self) -> str:
        return "Analyzes the sentiment of a given text, adapting the approach based on model capabilities"

    def run(self, llm: BaseLLM) -> TestResult:
        has_structured_output = "structured_output" in llm.capabilities()

        try:
            if has_structured_output:
                prompt = f"""You are a sentiment analysis expert. Analyze the sentiment of the following text and respond with a JSON object containing:
                - sentiment: either 'positive', 'negative', or 'neutral'
                - confidence: a float between 0 and 1
                - explanation: a brief explanation of your reasoning

                Text to analyze: "{self.text}"
                """
                query = {
                    "response_format": SentimentAnalysisResponse,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            else:
                prompt = f"""You are a sentiment analysis expert. Your task is to analyze the sentiment of text and respond with exactly one word: either POSITIVE, NEGATIVE, or NEUTRAL. Do not include any other text in your response.

                Text to analyze: {self.text}
                """
                query = {
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            
            response = llm.query(query)
            return TestResult(
                details=response,
                success=True
            )
        except Exception as e:
            return TestResult(
                details={"error": str(e)},
                success=False
            )
