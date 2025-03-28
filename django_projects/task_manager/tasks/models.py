from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Task(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.BooleanField(max_length=20, default='pending')

    def __str__(self):
        return self.title