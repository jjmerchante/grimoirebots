"""Cauldron2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from CauldronApp import views

urlpatterns = [
    path('github-login', views.github_login_callback),
    path('logout', views.github_logout),
    path('create-dashboard', views.create_dashboard),
    path('dashboard/<int:dash_id>', views.show_dashboard_info),
    path('dashboard-logs/<int:dash_id>', views.dash_logs),
    path('dashboard-status/<int:dash_id>', views.dash_status),
    path('', views.homepage),
    path('admin/', admin.site.urls),
]
