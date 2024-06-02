#!/bin/bash

# Update and install necessary packages
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Create and activate a virtual environment
python3 -m venv aenzbi_env
source aenzbi_env/bin/activate

# Install Django and Django REST framework
pip install django djangorestframework channels

# Create a new Django project and application
django-admin startproject aenzbi_project
cd aenzbi_project
django-admin startapp accounting

# Add the app to the project's settings
echo "
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'accounting',
    'channels',
]

# Channels settings
ASGI_APPLICATION = 'aenzbi_project.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
" >> aenzbi_project/settings.py

# Create initial models
cat <<EOT >> accounting/models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

class Transaction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
EOT

# Create serializers
cat <<EOT >> accounting/serializers.py
from rest_framework import serializers
from .models import Product, Transaction

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
EOT

# Create views
cat <<EOT >> accounting/views.py
from rest_framework import viewsets
from .models import Product, Transaction
from .serializers import ProductSerializer, TransactionSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
EOT

# Create routing for the APIs
cat <<EOT >> accounting/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
EOT

# Include the app URLs in the project's URLs
sed -i "/from django.urls import path/i from django.urls import include" aenzbi_project/urls.py
sed -i "/urlpatterns = \[/a \ \ \ \ path('api/', include('accounting.urls'))," aenzbi_project/urls.py

# Set up Django Channels
cat <<EOT > aenzbi_project/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import accounting.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aenzbi_project.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                accounting.routing.websocket_urlpatterns
            )
        )
    ),
})
EOT

# Create Channels routing for the app
mkdir accounting/routing
cat <<EOT > accounting/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/sync/', consumers.SyncConsumer.as_asgi()),
]
EOT

# Create a simple consumer for real-time updates
cat <<EOT > accounting/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer

class SyncConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def receive(self, text_data):
        data = json.loads(text_data)
        # Handle incoming data and update models
        self.send(text_data=json.dumps({
            'message': 'Data received'
        }))
EOT

# Migrate the database and create a superuser
python manage.py migrate
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'password')" | python manage.py shell

# Run the development server
echo "Setup complete. You can now run the server with: python manage.py runserver"
