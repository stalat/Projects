from django.db import models

# Create your models here.
class CustomerDetail(models.Model):
    name = models.CharField(max_length=100)
    email_account = models.EmailField()
    message = models.CharField(max_length=500, blank=True, null=True)
