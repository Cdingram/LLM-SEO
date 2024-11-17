# tasks/llm_tasks.py
from django_q.tasks import async_task
from core.llms.factory import get_llm
from core.models import TestRun, LLMModel
from core.llms.tests.registry import test_registry
from django.db.models import F
import logging

logger = logging.getLogger(__name__)

def run_test(test_run_id: str, llm_model_id: str, test_name: str) -> dict:
    llm_model = LLMModel.objects.get(id=llm_model_id)
    test_run = TestRun.objects.get(id=test_run_id)
    
    llm = get_llm(llm_model)
    test_class = test_registry._tests[test_name]
    
    test = test_class(text=test_run.domain_or_product)
    
    try:
        result = test.run(llm)
        return {
            'test_name': test.test_name,
            'success': result.success,
            'details': result.details
        }
    except Exception as e:
        return {
            'test_name': test.test_name,
            'success': False,
            'error': str(e)
        }
    
def execute_llm_test(test_run_id: str, llm_model_id: str) -> None:
    logger.info(f"Executing LLM test for test_run: {test_run_id}, model: {llm_model_id}")
    llm_model = LLMModel.objects.get(id=llm_model_id)    
    
    # Get test classes from registry
    available_test_classes = test_registry.get_available_tests(llm_model)
    
    # Spawn individual test tasks
    for test_class in available_test_classes:
        test_name = test_class.test_name()
        task_name = f"single_test_{test_run_id}_{llm_model_id}_{test_name}"
        logger.info(f"Spawning individual test: {task_name}")
        async_task(
            'core.tasks.llm_tasks.run_test',
            test_run_id,
            llm_model_id,
            test_name,
            task_name=task_name,
            hook='core.tasks.llm_tasks.test_complete'
        )

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