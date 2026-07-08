from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    """الصفحة الرئيسية"""
    return render(request, 'dashboard/index.html')