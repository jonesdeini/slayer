from django.contrib import admin

from board.services import create_lead

from .models import ScrapedJob, WatchedCompany


@admin.register(WatchedCompany)
class WatchedCompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'board_token', 'keywords', 'is_active']
    search_fields = ['name', 'board_token']


@admin.action(description='Promote selected jobs to a Lead')
def promote_to_lead(modeladmin, request, queryset):
    promoted = 0
    for job in queryset:
        if job.promoted_lead_id:
            continue
        lead = create_lead(
            company_name=job.watched_company.name,
            role_title=job.title,
            job_url=job.absolute_url,
        )
        job.promoted_lead = lead
        job.save(update_fields=['promoted_lead'])
        promoted += 1
    modeladmin.message_user(request, f'Promoted {promoted} job(s) to leads.')


@admin.register(ScrapedJob)
class ScrapedJobAdmin(admin.ModelAdmin):
    list_display = ['title', 'watched_company', 'location', 'is_active', 'promoted_lead', 'last_seen_at']
    list_filter = ['is_active', 'watched_company']
    search_fields = ['title', 'watched_company__name']
    actions = [promote_to_lead]
