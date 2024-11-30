from typing import List
from .base import BaseLLMTest, TestResult
from .sentiment import SentimentAnalysisTest
from core.llms.adapters.base import BaseLLM
from django.conf import settings

class ProductSentimentAnalysisTest(BaseLLMTest):
    required_capabilities = ["chat"]

    def __init__(self, product: str, product_category: str, product_description: str):
        self.product = product
        self.product_category = product_category
        self.product_description = product_description

    @classmethod
    def test_name(cls) -> str:
        return "product_sentiment_analysis"

    @property
    def description(self) -> str:
        return "Analyzes sentiment of opinions and reviews about the product"

    def _get_product_opinions(self, llm: BaseLLM) -> List[dict]:
        prompts = [
            f"What do users generally think about {self.product}?",
            f"Can you provide an honest review of {self.product} for {self.product_description}?",
            f"What are the main pros and cons of using {self.product}?",
            f"How do customers feel about {self.product} compared to other {self.product_category} solutions?",
            f"What's your assessment of {self.product}'s strengths and weaknesses?"
        ]
        
        opinions = []
        for prompt in prompts:
            query = {"messages": [{"role": "user", "content": prompt}]}
            response = llm.query(query)
            processed = llm.process_response(response)
            opinions.append({
                "prompt": prompt,
                "response": processed
            })
        return opinions

    def run(self, llm: BaseLLM) -> TestResult:
        try:
            # Get opinions using the provided LLM
            opinions = self._get_product_opinions(llm)
            
            # Use analysis LLM for sentiment analysis
            analysis_llm = self.get_analysis_llm()
            sentiment_analyzer = SentimentAnalysisTest("")
            sentiment_results = []
            
            for opinion in opinions:
                sentiment_analyzer.text = opinion["response"]
                # Use analysis_llm instead of provided llm
                sentiment_result = sentiment_analyzer.run(analysis_llm)
                
                if not sentiment_result.success:
                    continue
                    
                sentiment_results.append({
                    "prompt": opinion["prompt"],
                    "response": opinion["response"],
                    "sentiment": sentiment_result.structured_data
                })

            # Calculate overall sentiment stats
            total_analyzed = len(sentiment_results)
            if total_analyzed == 0:
                raise Exception("No successful sentiment analyses")

            sentiment_counts = {
                "positive": sum(1 for r in sentiment_results if r["sentiment"]["sentiment"].lower() == "positive"),
                "neutral": sum(1 for r in sentiment_results if r["sentiment"]["sentiment"].lower() == "neutral"),
                "negative": sum(1 for r in sentiment_results if r["sentiment"]["sentiment"].lower() == "negative")
            }

            # Determine overall sentiment
            max_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])
            overall_sentiment = max_sentiment[0]
            sentiment_ratio = max_sentiment[1] / total_analyzed

            readable_response = (
                f"Analysis of {total_analyzed} opinions about {self.product}:\n\n"
                f"Overall sentiment: {overall_sentiment.upper()} "
                f"({sentiment_counts['positive']} positive, "
                f"{sentiment_counts['neutral']} neutral, "
                f"{sentiment_counts['negative']} negative)\n\n"
                "Key opinions:\n"
            )

            # Add most representative opinions for the overall sentiment
            matching_sentiment = [r for r in sentiment_results 
                                if r["sentiment"]["sentiment"].lower() == overall_sentiment]
            if matching_sentiment:
                readable_response += f"- {matching_sentiment[0]['response']}\n"

            return TestResult(
                success=True,
                readable_response=readable_response,
                raw_responses=[{"opinions": opinions}] if settings.STORE_RAW_RESPONSES else None,
                structured_data={
                    "overall_sentiment": overall_sentiment,
                    "confidence": sentiment_ratio,
                    "sentiment_distribution": sentiment_counts,
                    "detailed_results": sentiment_results
                },
                metadata={
                    "product_category": self.product_category,
                    "total_opinions": total_analyzed
                }
            )

        except Exception as e:
            return TestResult(
                success=False,
                error=str(e)
            )

# from core.models import LLMModel, LLMProvider
# from core.llms.factory import get_llm
# from core.llms.tests.sentiment_analysis import ProductSentimentAnalysisTest

# provider = LLMProvider.objects.get(name="OpenAI")
# model = LLMModel.objects.filter(
#     provider=provider,
#     is_active=True
# ).first()
# llm = get_llm(model)
# test = ProductSentimentAnalysisTest(
#     product="PhotoAI.com",
#     product_category="AI Photography",
#     product_description="giving you a full photoshoot created with AI"
# )
# result = test.run(llm)