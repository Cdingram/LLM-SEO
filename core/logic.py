from django.db import transaction
from django_q.tasks import async_task
from django_q.models import Task
from django.db.models import F
from .models import TestRun, LLMModel, Profile
from .llms.tests.registry import test_registry

def initiate_test_run(product: str, product_category: str, product_description: str, profile: Profile | None = None) -> TestRun:
    """Creates a new test run and queues the testing process."""
    active_models = LLMModel.objects.filter(is_active=True)

    with transaction.atomic():
        test_run = TestRun.objects.create(
            profile=profile,
            product=product,
            product_category=product_category,
            product_description=product_description,
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

    # Spawn individual test tasks directly for each model
    for model in active_models:
        available_test_classes = test_registry.get_available_tests(model)
        for test_class in available_test_classes:
            test_name = test_class.test_name()
            task_name = f"test_{test_run.id}_{model.id}_{test_name}"
            async_task(
                'core.tasks.llm_tasks.run_test',
                test_run.id,
                model.id,
                test_name,
                task_name=task_name,
                hook='core.tasks.llm_tasks.test_complete'
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
