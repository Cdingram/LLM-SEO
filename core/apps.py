from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import here to avoid circular imports
        from .llms.registry import provider_registry
        from .llms.adapters.openai import OpenAI
        from .llms.tests import MentionFrequencyTest, FeatureRecognitionTest, ProductSentimentAnalysisTest, CompetitorComparisonTest
        from .llms.tests.registry import test_registry
        
        # providers registry
        provider_registry.register("OpenAI", OpenAI)
        
        # tests registry
        test_registry.register(MentionFrequencyTest)
        test_registry.register(FeatureRecognitionTest)
        test_registry.register(ProductSentimentAnalysisTest)
        test_registry.register(CompetitorComparisonTest)