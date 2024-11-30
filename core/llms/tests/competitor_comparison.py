from typing import List, Dict
from .base import BaseLLMTest, TestResult
from core.llms.adapters.base import BaseLLM
from pydantic import BaseModel
from django.conf import settings

class CompetitorComparisonTest(BaseLLMTest):
    required_capabilities = ["chat"]

    def __init__(self, product: str, product_category: str, product_description: str):
        self.product = product
        self.product_category = product_category
        self.product_description = product_description

    @classmethod
    def test_name(cls) -> str:
        return "competitor_comparison"

    @property
    def description(self) -> str:
        return "Analyzes and compares the product against its main competitors"

    def _get_top_competitors(self, llm: BaseLLM) -> List[str]:
        competitor_prompt = f"""Who are the top 3-5 direct competitors of {self.product}?
        The product offers: {self.product_description}
        
        Return just the names separated by '|' (e.g., 'Competitor1|Competitor2|Competitor3')"""

        query = {"messages": [{"role": "user", "content": competitor_prompt}]}
        response = llm.query(query)
        competitors = llm.process_response(response).strip().split("|")
        return [comp.strip() for comp in competitors if comp.strip()]

    def _get_competitor_comparison(self, llm: BaseLLM, competitor: str) -> tuple[List[str], List[str]]:
        comparison_prompts = [
            f"What are the main advantages of {competitor} compared to {self.product}?",
            f"What are the main advantages of {self.product} compared to {competitor}?",
            f"In 2-3 sentences, what are the key differences between {self.product} and {competitor}?",
            f"How does {competitor} stack up against {self.product} for {self.product_description}?",
            f"Which is better, {competitor} or {self.product}?",
            f"How does {competitor} compare to {self.product}?"
        ]
        
        responses = []
        for prompt in comparison_prompts:
            query = {"messages": [{"role": "user", "content": prompt}]}
            response = llm.query(query)
            responses.append(llm.process_response(response))
        
        return responses, comparison_prompts

    def run(self, llm: BaseLLM) -> TestResult:
        try:
            competitors = self._get_top_competitors(llm)
            readable_response = f"Quick comparison of {self.product}'s competitors:\n\n"
            structured_data = {"comparisons": []}
            raw_responses = []
            
            analysis_llm = self.get_analysis_llm()
            
            for competitor in competitors:
                responses, prompts = self._get_competitor_comparison(llm, competitor)
                
                # Store raw responses
                for prompt, response in zip(prompts, responses):
                    raw_responses.append({
                        "prompt": prompt,
                        "response": response
                    })
                
                # Create a summary prompt using all responses
                summary_prompt = f"""Based on these detailed comparisons between {self.product} and {competitor}, provide a 1-2 sentence summary highlighting only the most important parts:

                Detailed comparisons:
                {' '.join(responses)}

                Summary:"""
                
                query = {"messages": [{"role": "user", "content": summary_prompt}]}
                summary_response = analysis_llm.query(query)
                summary = analysis_llm.process_response(summary_response)
                raw_responses.append({
                    "prompt": summary_prompt,
                    "response": summary_response
                })
                
                readable_response += f"**{competitor}**: {summary}\n\n"
                
                # Store structured data with new format
                structured_data["comparisons"].append({
                    "name": competitor,
                    "data": {
                        "summary": summary,
                        "detailed_responses": [
                            {
                                "question": prompt,
                                "answer": self._get_response_summary(llm, prompt, response)
                            } for prompt, response in zip(prompts, responses)
                        ]
                    }
                })

            return TestResult(
                success=True,
                readable_response=readable_response,
                raw_responses=raw_responses if settings.STORE_RAW_RESPONSES else None,
                structured_data=structured_data,
                metadata={
                    "product_category": self.product_category,
                    "competitor_count": len(competitors)
                }
            )

        except Exception as e:
            return TestResult(
                success=False,
                error=str(e)
            )

    def _get_response_summary(self, llm: BaseLLM, prompt: str, response: str) -> str:
        analysis_llm = self.get_analysis_llm()
        summary_prompt = f"""Summarize this response in 1-2 sentences, focusing on the key points:

        Question: {prompt}
        Response: {response}

        Summary:"""
        
        query = {"messages": [{"role": "user", "content": summary_prompt}]}
        return analysis_llm.process_response(analysis_llm.query(query))

# from core.models import LLMModel, LLMProvider
# from core.llms.factory import get_llm
# from core.llms.tests.competitor_comparison import CompetitorComparisonTest

# provider = LLMProvider.objects.get(name="OpenAI")
# model = LLMModel.objects.filter(
#             provider=provider,
#             is_active=True
#         ).first()
# llm = get_llm(model)
# test = CompetitorComparisonTest(
#             product="PhotoAI.com",
#             product_category="Consumer website",
#             product_description="Ai photographer/photoshoot"
#         )
# result = test.run(llm)