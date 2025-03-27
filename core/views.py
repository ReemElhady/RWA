from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import City
# Create your views here.

@login_required
def dashboard(request):
    cities = City.objects.all()
    return render(request,'index.html',{'cities':cities})
