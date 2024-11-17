from django.contrib import admin
from .models import Profile, LLMProvider, LLMModel, TestRun

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
    list_display = ('provider', 'model_name', 'is_active', 'date_created', 'date_modified')
    readonly_fields = ('date_created', 'date_modified')
    list_filter = ('provider', 'is_active')
    search_fields = ('provider__name', 'model_name')

@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'domain_or_product', 'status', 'total_tests', 'completed_tests', 'date_created')
    readonly_fields = ('date_created', 'date_modified')
    list_filter = ('status',)
    search_fields = ('id', 'domain_or_product', 'profile__user__username')
