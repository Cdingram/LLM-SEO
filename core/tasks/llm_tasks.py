# tasks/llm_tasks.py
from django_q.tasks import async_task
from core.llms.factory import get_llm
from core.models import TestRun, LLMModel, TestResult
from core.llms.tests.registry import test_registry
from django.db.models import F
import logging

logger = logging.getLogger(__name__)

def run_test(test_run_id: str, llm_model_id: str, test_name: str) -> dict:
    llm_model = LLMModel.objects.get(id=llm_model_id)
    test_run = TestRun.objects.get(id=test_run_id)
    
    # Create TestResult record
    test_result = TestResult.objects.create(
        test_run=test_run,
        llm_model=llm_model
    )
    
    llm = get_llm(llm_model)
    test_class = test_registry._tests[test_name]
    test = test_class(product=test_run.product, product_category=test_run.product_category, product_description=test_run.product_description)
    
    try:
        result = test.run(llm)
        test_result.success = result.success
        test_result.readable_response = result.readable_response
        test_result.raw_responses = result.raw_responses
        test_result.structured_data = result.structured_data
        test_result.metadata = result.metadata
        test_result.error = result.error
        test_result.test_name = test_name
        test_result.save()
        
        return test_result.id
    except Exception as e:
        # Update test result with the error
        test_result.success = False
        test_result.error = str(e)
        test_result.test_name = test_name
        test_result.save()
        
        return test_result.id
    
def test_complete(task):
    """Hook that runs when an individual test completes"""
    test_run_id = task.args[0]  # First argument was test_run_id
    
    test_run = TestRun.objects.get(id=test_run_id)
    
    # Check if the task failed
    if task.success is False:
        test_run.status = TestRun.Status.FAILED
        test_run.save()
        logger.error(f"Test run {test_run_id} failed: {task.result}")
        return
    
    test_run.completed_tests = F('completed_tests') + 1
    test_run.save()
    
    # Refresh from database to get actual values
    test_run.refresh_from_db()
    
    # Check if all tests are complete
    if test_run.completed_tests == test_run.total_tests:
        test_run.status = TestRun.Status.COMPLETED
        test_run.save()