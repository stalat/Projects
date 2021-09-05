from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ProductSerializer
from .models import Product, User
import random
# Create your views here.


class ProductViewSet(viewsets.ViewSet):
    def list(self, request):  # /api/products
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def create(self, request):  # /api/products/<str:id>
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):  # /api/products/<str:id>
        product_data = Product.objects.get(id=pk)
        serializer = ProductSerializer(product_data)
        return Response(serializer.data)

    def update(self, request, pk=None):  # /api/products/<str:id>
        product_data = Product.objects.get(id=pk)
        serializer = ProductSerializer(instance=product_data, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, pk=None):  # /api/products/<str:id>
        product_data = Product.objects.get(id=pk)
        product_data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAPIView(APIView):
    def get(self, _):
        users = User.objects.all()
        user = random.choice(users)
        return Response({
            'id': user.id,
        })
