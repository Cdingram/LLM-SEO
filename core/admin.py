from django.contrib import admin
from .models import Profile, LLMProvider, LLMModel, TestRun, TestResult

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'date_created', 'date_modified')
    readonly_fields = ('date_created', 'date_modified')
    search_fields = ('user__username', 'id')

@admin.register(LLMProvider)
class LLMProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_created', 'date_modified')
    readonly_fields = ('date_created', 'date_modified')
    search_fields = ('name',)

@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ('provider', 'model_name', 'is_active', 'capabilities', 'date_created', 'date_modified')
    readonly_fields = ('date_created', 'date_modified')
    list_filter = ('provider', 'is_active', 'capabilities')
    search_fields = ('provider__name', 'model_name')

@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'product', 'status', 'total_tests', 'completed_tests', 'date_created')
    readonly_fields = ('date_created', 'date_modified')
    list_filter = ('status', 'product_category')
    search_fields = ('id', 'product', 'profile__user__username', 'product_category', 'product_description')

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'test_run', 'llm_model', 'test_name', 'success', 'date_created')
    readonly_fields = ('date_created',)
    list_filter = ('success', 'test_name', 'llm_model')
    search_fields = ('id', 'test_run__id', 'test_name', 'llm_model__model_name', 'error', 'readable_response')

