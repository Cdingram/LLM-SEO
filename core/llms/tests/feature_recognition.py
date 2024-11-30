from typing import List
from .base import BaseLLMTest, TestResult
from core.llms.adapters.base import BaseLLM
from pydantic import BaseModel
from django.conf import settings
from openai.lib._pydantic import to_strict_json_schema
import json

class FeatureAnalysisResponse(BaseModel):
    primary_purpose: str
    key_features: List[str]
    target_users: str

class FeatureRecognitionTest(BaseLLMTest):
    required_capabilities = ["chat"]

    def __init__(self, product: str, product_category: str, product_description: str):
        self.product = product
        self.product_category = product_category
        self.product_description = product_description

    @classmethod
    def test_name(cls) -> str:
        return "feature_recognition"

    @property
    def description(self) -> str:
        return "Analyzes how accurately the LLM recognizes and describes the product's key features and benefits"

    def _get_feature_responses(self, llm: BaseLLM) -> List[dict]:
        prompts = [
            f"What are the main features of {self.product}?",
            f"What does {self.product} do?",
            f"What is {self.product} good for?",
            f"What makes {self.product} unique in {self.product_category}?",
            f"What are the key benefits of using {self.product}?",
            f"How does {self.product} help users with {self.product_description}?",
            f"What problems does {self.product} solve?"
        ]
        
        responses = []
        for prompt in prompts:
            query = {"messages": [{"role": "user", "content": prompt}]}
            response = llm.query(query)
            responses.append({
                "prompt": prompt,
                "response": llm.process_response(response)
            })
        return responses

    def run(self, llm: BaseLLM) -> TestResult:
        try:
            # Get initial feature responses
            feature_responses = self._get_feature_responses(llm)
            
            # Use analysis LLM to compile/summarize responses
            analysis_llm = self.get_analysis_llm()
            has_structured_output = "structured_output" in analysis_llm.capabilities()
            
            # Create analysis prompt
            if has_structured_output:
                analysis_prompt = f"""Based on these responses about {self.product}, compile a clear summary of what the LLM thinks this product's features and purpose are.
                
                Responses to analyze:
                {chr(10).join(f'- {resp["response"]}' for resp in feature_responses)}
                
                Provide a JSON response with:
                {{
                    "primary_purpose": "main purpose/function of the product",
                    "key_features": [list of main features mentioned consistently],
                    "target_users": "who the product seems designed for"
                }}"""
                
                query = {
                    "response_format": to_strict_json_schema(FeatureAnalysisResponse),
                    "messages": [{"role": "user", "content": analysis_prompt}]
                }
            else:
                analysis_prompt = f"""Based on these responses about {self.product}, compile a clear summary in exactly this format:
                PRIMARY PURPOSE: <main purpose>
                KEY FEATURES: feature1|feature2|feature3
                TARGET USERS: <target users>

                Responses to analyze:
                {chr(10).join(f'- {resp["response"]}' for resp in feature_responses)}"""
                
                query = {"messages": [{"role": "user", "content": analysis_prompt}]}

            analysis_response = analysis_llm.query(query)
            analysis_text = analysis_llm.process_response(analysis_response)

            # If we got structured output, use it directly
            if has_structured_output and isinstance(analysis_text, dict):
                analysis = analysis_text
            else:
                # Parse the formatted string response
                lines = analysis_text.strip().split('\n')
                analysis = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()
                        if key in ['key_features']:
                            analysis[key] = [v.strip() for v in value.split('|') if v.strip()]
                        else:
                            analysis[key] = value

            # Rest of the code remains the same
            structured_data = {
                "compiled_understanding": analysis
            }

            readable_response = f"""LLM's Understanding of {self.product}:

            Primary Purpose:
            {analysis.get('primary_purpose', 'N/A')}

            Key Features:
            {chr(10).join(f'- {feature}' for feature in analysis.get('key_features', []))}

            Target Users:
            {analysis.get('target_users', 'N/A')}"""

            return TestResult(
                success=True,
                readable_response=readable_response,
                raw_responses=[{"responses": feature_responses, "analysis": analysis}] if settings.STORE_RAW_RESPONSES else None,
                structured_data=structured_data,
                metadata={
                    "product_category": self.product_category,
                    "total_prompts": len(feature_responses)
                }
            )

        except Exception as e:
            return TestResult(
                success=False,
                error=str(e)
            )

# from core.models import LLMModel, LLMProvider
# from core.llms.factory import get_llm
# from core.llms.tests.feature_recognition import FeatureRecognitionTest

# provider = LLMProvider.objects.get(name="OpenAI")
# model = LLMModel.objects.filter(
#     provider=provider,
#     is_active=True
# ).first()
# llm = get_llm(model)
# test = FeatureRecognitionTest(
#     product="PhotoAI.com",
#     product_category="AI Photography",
#     product_description="giving you a full photoshoot created with AI"
# )
# result = test.run(llm)