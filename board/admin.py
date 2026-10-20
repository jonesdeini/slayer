from django.contrib import admin

from .models import Company, Lead


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'created_at']
    search_fields = ['name']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['role_title', 'company', 'status', 'applied_at', 'updated_at']
    list_filter = ['status']
    search_fields = ['role_title', 'company__name']
    autocomplete_fields = ['company']
