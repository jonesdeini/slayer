import requests
from django.core.management.base import BaseCommand

from crawler.models import ScrapedJob, WatchedCompany

GREENHOUSE_URL = 'https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true'


class Command(BaseCommand):
    help = 'Fetch jobs from each active WatchedCompany Greenhouse board and upsert ScrapedJob rows.'

    def handle(self, *args, **options):
        for watched in WatchedCompany.objects.filter(is_active=True):
            self.crawl_company(watched)

    def crawl_company(self, watched):
        response = requests.get(GREENHOUSE_URL.format(token=watched.board_token), timeout=30)
        if response.status_code != 200:
            self.stderr.write(
                f'{watched.name}: Greenhouse returned {response.status_code}, skipping'
            )
            return

        jobs = response.json().get('jobs', [])
        keywords = watched.keyword_list()
        seen_ids = set()

        for job in jobs:
            if keywords and not any(k in job['title'].lower() for k in keywords):
                continue
            seen_ids.add(job['id'])
            ScrapedJob.objects.update_or_create(
                greenhouse_id=job['id'],
                defaults={
                    'watched_company': watched,
                    'title': job['title'],
                    'location': (job.get('location') or {}).get('name', ''),
                    'absolute_url': job.get('absolute_url', ''),
                    'content': job.get('content', ''),
                    'is_active': True,
                },
            )

        stale = ScrapedJob.objects.filter(watched_company=watched, is_active=True).exclude(
            greenhouse_id__in=seen_ids
        )
        stale_count = stale.update(is_active=False)

        self.stdout.write(
            f'{watched.name}: {len(seen_ids)} active job(s), {stale_count} marked inactive'
        )
