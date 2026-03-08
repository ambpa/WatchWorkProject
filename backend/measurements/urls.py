# measurement/urls.py

from django.urls import path
from .views import receive_data

urlpatterns = [
    path("data/", receive_data),
]
