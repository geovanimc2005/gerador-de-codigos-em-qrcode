from . import views
from django.urls import *
from django.contrib import admin
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meu_app.urls')),
    path('minha_url/', views.minha_view, name='minha_view'),
    path('', include('meu_aplicativo.urls')),
]