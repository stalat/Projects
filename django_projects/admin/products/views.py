from django.shortcuts import render
from rest_framework import viewsets
from .serializers import ProductSerializer
# Create your views here.


class ProductViewSet(viewsets.ViewSet):
    def list(self, request):  # /api/products
        pass

    def create(self, request):  # /api/products/<str:id>
        pass

    def retrieve(self, request, pk=None):  # /api/products/<str:id>
        pass

    def update(self, request, pk=None):  # /api/products/<str:id>
        pass

    def destroy(self, request, pk=None):  # /api/products/<str:id>
        pass
