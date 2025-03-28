from django.db import models

class ProductManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)

class Product(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    objects = ProductManager()
