"""
URL configuration for slayer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from board.api import CompanyViewSet, LeadViewSet

router = DefaultRouter()
router.register('companies', CompanyViewSet)
router.register('leads', LeadViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('board.urls')),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
