from django.db import transaction
from django_q.tasks import async_task
from django_q.models import Task
from django.db.models import F
from .models import TestRun, LLMModel, Profile
from .tasks.llm_tasks import execute_llm_test
from .llms.tests.registry import test_registry

def initiate_test_run(target: str, profile: Profile | None = None) -> TestRun:
    """Creates a new test run and queues the testing process."""
    active_models = LLMModel.objects.filter(is_active=True)

    with transaction.atomic():
        test_run = TestRun.objects.create(
            profile=profile,
            domain_or_product=target,
            status=TestRun.Status.IN_PROGRESS,
            total_tests=0
        )
        
        # Calculate and set total tests atomically
        total_tests = 0
        for model in active_models:
            available_tests = test_registry.get_available_tests(model)
            total_tests += len(available_tests)
        
        test_run.total_tests = total_tests
        test_run.save()

    # Queue each LLM test independently
    for model in active_models:
        task_name = f"llm_test_{test_run.id}_{model.id}"
        async_task(
            execute_llm_test,
            test_run.id,
            model.id,
            task_name=task_name
        )

    return test_run

def test_run_complete(task: Task):
    print(task.result)

def get_test_run_progress(test_run_id: str) -> dict:
    """Gets the current progress of a test run."""
    try:
        test_run = TestRun.objects.get(id=test_run_id)
        progress = (test_run.completed_tests / test_run.total_tests * 100) if test_run.total_tests > 0 else 0
        
        return {
            'status': test_run.status,
            'total_tests': test_run.total_tests,
            'completed_tests': test_run.completed_tests,
            'progress_percentage': round(progress, 2),
            'results': list(test_run.results.values(
                'llm_model__model_name',
                'processed_data'
            )) if test_run.status == TestRun.Status.COMPLETED else []
        }
    except TestRun.DoesNotExist:
        return {'error': 'Test run not found'}
