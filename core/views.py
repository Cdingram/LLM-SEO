from django.shortcuts import render
from django.views import View
from django.contrib.sites.models import Site
from django.http import JsonResponse
from core.logic import get_test_run_progress

# Create your views here.
class Home(View):

    def get(self, request):
        return render(request, "core/index.html", {"current_site": Site.objects.get_current()})

def check_test_progress(request, test_run_id):
    progress = get_test_run_progress(test_run_id)
    return JsonResponse(progress)