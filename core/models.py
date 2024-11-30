from django.db import models
from django.contrib.auth.models import User
from shortuuid.django_fields import ShortUUIDField
from django.db.models.signals import post_save
from django.dispatch import receiver
from multiselectfield import MultiSelectField

class Profile(models.Model):
    id = ShortUUIDField(primary_key=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
    
    class Meta:
        ordering = ['-date_created']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile when a new User is created."""
    if created:
        Profile.objects.create(user=instance)
    
class LLMProvider(models.Model):
    id = ShortUUIDField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date_created']

class LLMModel(models.Model):
    class Capabilities(models.TextChoices):
        CHAT = 'chat', 'Chat'
        STRUCTURED_OUTPUT = 'structured_output', 'Structured Output'
        FUNCTION_CALLING = 'function_calling', 'Function Calling'
        CODE = 'code', 'Code Generation'
        EMBEDDINGS = 'embeddings', 'Embeddings'

    id = ShortUUIDField(primary_key=True)
    provider = models.ForeignKey(LLMProvider, on_delete=models.CASCADE, related_name="models")
    model_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    capabilities = MultiSelectField(
        choices=Capabilities.choices,
        max_length=255,
        default=Capabilities.CHAT
    )

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']
        unique_together = ('provider', 'model_name')

    def __str__(self):
        return f"{self.provider.name} - {self.model_name}"

class TestRun(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = ShortUUIDField(primary_key=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    product = models.CharField(max_length=255)
    product_category = models.CharField(max_length=255, null=True, blank=True)
    product_description = models.TextField(null=True, blank=True)

    status = models.CharField(
        max_length=20, 
        choices=Status.choices,
        default=Status.PENDING
    )
    total_tests = models.IntegerField(default=0)
    completed_tests = models.IntegerField(default=0)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']

class TestResult(models.Model):
    id = ShortUUIDField(primary_key=True)
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='results')
    llm_model = models.ForeignKey(LLMModel, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=100)
    success = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    readable_response = models.TextField(null=True, blank=True)
    raw_responses = models.JSONField(null=True, blank=True)
    structured_data = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']
