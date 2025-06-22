from django.http import *
from .models import *
def minha_view(request):
    return HttpResponse('olá mundo')