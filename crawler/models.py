from django.db import models

from board.models import Lead


class WatchedCompany(models.Model):
    name = models.CharField(max_length=255)
    board_token = models.SlugField(
        max_length=255, unique=True,
        help_text='Greenhouse board token, e.g. the "acme" in boards.greenhouse.io/acme',
    )
    keywords = models.CharField(
        max_length=500, blank=True,
        help_text='Comma-separated keywords to filter job titles by; empty means no filter',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'watched companies'

    def __str__(self):
        return self.name

    def keyword_list(self):
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]


class ScrapedJob(models.Model):
    watched_company = models.ForeignKey(
        WatchedCompany, on_delete=models.CASCADE, related_name='jobs',
    )
    greenhouse_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=500)
    location = models.CharField(max_length=255, blank=True)
    absolute_url = models.URLField(max_length=1000)
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    promoted_lead = models.OneToOneField(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_job',
    )

    class Meta:
        ordering = ['-last_seen_at']

    def __str__(self):
        return f'{self.title} @ {self.watched_company.name}'
