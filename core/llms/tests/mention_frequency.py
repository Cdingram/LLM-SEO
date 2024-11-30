from typing import List
from .base import BaseLLMTest, TestResult
from core.llms.adapters.base import BaseLLM
from pydantic import BaseModel
from django.conf import settings
from openai.lib._pydantic import to_strict_json_schema

class MentionFrequencyResponse(BaseModel):
    brand_mentions: int
    competitor_mentions: int
    mentioned_competitors: List[str]
    analysis: str
    brand_keywords: List[str]
    competitor_keywords: List[str]

class MentionFrequencyTest(BaseLLMTest):
    required_capabilities = ["chat"]

    def __init__(self, product: str, product_category: str, product_description: str):
        self.product = product
        self.product_category = product_category
        self.product_description = product_description

    @classmethod
    def test_name(cls) -> str:
        return "mention_frequency"

    @property
    def description(self) -> str:
        return "Analyzes how frequently a brand is mentioned compared to competitors in product category discussions"

    def run(self, llm: BaseLLM) -> TestResult:
        try:
            # List of prompts focused on specific use cases and product description
            prompts = [
                f"I need a solution for {self.product_description}. What would you recommend?",
                f"What's the best tool for this requirement: {self.product_description}?",
                f"Can you suggest solutions that would help me {self.product_description.lower()}?",
                f"I'm looking for software that can {self.product_description.lower()}. What are my options?",
                f"What are the leading platforms in {self.product_category} that can {self.product_description.lower()}?",
                f"Which tools would you recommend for {self.product_description.lower()}? Please compare the top options.",
                f"What's the best solution if I want to {self.product_description.lower()}? Please explain the pros and cons.",
                f"I'm evaluating different options for {self.product_description.lower()}. What should I consider?"
            ]

            # Get initial responses using provided LLM
            prompt_responses = []
            for prompt in prompts:
                query = {"messages": [{"role": "user", "content": prompt}]}
                response = llm.query(query)
                processed = llm.process_response(response)
                prompt_responses.append({
                    "prompt": prompt,
                    "response": processed
                })

            # Use analysis LLM for analysis
            analysis_llm = self.get_analysis_llm()
            has_structured_output = "structured_output" in analysis_llm.capabilities()
            
            # Analysis prompt remains the same but uses analysis_llm
            if has_structured_output:
                analysis_prompt = f"""Analyze these responses to questions about {self.product_category}. Count mentions of {self.product} versus competitor brands. Respond with a JSON object containing:
                - brand_mentions: number of times {self.product} is mentioned
                - competitor_mentions: total number of times other brands are mentioned
                - mentioned_competitors: list of competitor brand names mentioned
                - analysis: brief analysis of the brand's presence in responses
                - brand_keywords: list of key terms/phrases associated with {self.product} in the responses (the most commonly used keywords across all of the responses)
                - competitor_keywords: list of key terms/phrases associated with competitor products

                Responses to analyze:
                {chr(10).join(f'- {resp["response"]}' for resp in prompt_responses)}
                """
                query = {
                    "response_format": to_strict_json_schema(MentionFrequencyResponse),
                    "messages": [
                        {"role": "user", "content": analysis_prompt}
                    ]
                }
            else:
                analysis_prompt = f"""Analyze these responses about {self.product_category} and provide the following information in exactly this format:
                [mentions of {self.product}],[total mentions of other brands],[competitor1,competitor2,etc],[brief analysis],[keyword1|keyword2|etc for {self.product} (the most commonly used keywords across all of the responses)],[keyword1|keyword2|etc for competitors (the most commonly used keywords across all of the responses)]

                For example: 3,5,Google Pixel|Huawei Nova 13|IPhone 16,Brand has moderate presence,AI camera|portrait mode,computational photography|night mode

                Responses:
                {chr(10).join(f'- {resp["response"]}' for resp in prompt_responses)}
                """
                query = {
                    "messages": [
                        {"role": "user", "content": analysis_prompt}
                    ]
                }

            analysis_response = analysis_llm.query(query)
            processed_analysis = analysis_llm.process_response(analysis_response)
            
            if has_structured_output:
                readable_response = (
                    f"Brand '{self.product}' was mentioned {processed_analysis.brand_mentions} times, "
                    f"while competitors were mentioned {processed_analysis.competitor_mentions} times. "
                    f"Main competitors mentioned: {', '.join(processed_analysis.mentioned_competitors)}. "
                    f"{processed_analysis.analysis}"
                )
            else:
                brand_mentions, competitor_mentions, competitors_str, analysis, brand_keywords_str, competitor_keywords_str = processed_analysis.split(',', 5)
                competitors = [c.strip() for c in competitors_str.split('|') if c.strip()]
                brand_keywords = [k.strip() for k in brand_keywords_str.split('|') if k.strip()]
                competitor_keywords = [k.strip() for k in competitor_keywords_str.split('|') if k.strip()]
                readable_response = (
                    f"Brand '{self.product}' was mentioned {brand_mentions} times, "
                    f"while competitors were mentioned {competitor_mentions} times. "
                    f"Main competitors mentioned: {', '.join(competitors)}. "
                    f"{analysis}"
                )

            structured_data = {
                "brand_stats": {
                    "brand_name": self.product,
                    "mention_count": processed_analysis.brand_mentions if has_structured_output else int(brand_mentions),
                    "competitor_mention_count": processed_analysis.competitor_mentions if has_structured_output else int(competitor_mentions),
                    "competitors": {
                        competitor: sum(1 for resp in prompt_responses 
                                     if competitor.lower() in resp["response"].lower())
                        for competitor in (processed_analysis.mentioned_competitors if has_structured_output else competitors)
                    },
                    "brand_keywords": processed_analysis.brand_keywords if has_structured_output else brand_keywords,
                    "competitor_keywords": processed_analysis.competitor_keywords if has_structured_output else competitor_keywords
                },
                "brand_mentions": [
                    {
                        "prompt": resp["prompt"],
                        "response": resp["response"]
                    }
                    for resp in prompt_responses
                    if self.product.lower() in resp["response"].lower()
                ]
            }

            return TestResult(
                success=True,
                readable_response=readable_response,
                raw_responses=[analysis_response] if settings.STORE_RAW_RESPONSES else None,
                structured_data=structured_data,
                metadata={
                    "product_category": self.product_category,
                    "total_prompts": len(prompts)
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                error=str(e)
            )


# from core.models import LLMModel, LLMProvider
# from core.llms.factory import get_llm
# from core.llms.tests.mention_frequency import MentionFrequencyTest

# provider = LLMProvider.objects.get(name="OpenAI")
# model = LLMModel.objects.filter(
#             provider=provider,
#             is_active=True
#         ).first()
# llm = get_llm(model)
# test = MentionFrequencyTest(
#             product="PhotoAI.com",
#             product_category="AI Photography",
#             product_description="giving you a full photoshoot created with AI"
#         )
# result = test.run(llm)
