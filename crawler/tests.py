from unittest.mock import Mock, patch

from django.test import TestCase

from board.models import Lead
from crawler.admin import promote_to_lead
from crawler.management.commands.crawl_greenhouse import Command
from crawler.models import ScrapedJob, WatchedCompany

FAKE_JOBS_RESPONSE = {
    'jobs': [
        {
            'id': 1,
            'title': 'Backend Engineer',
            'location': {'name': 'Remote'},
            'absolute_url': 'https://example.com/jobs/1',
            'content': 'do backend things',
        },
        {
            'id': 2,
            'title': 'Sales Rep',
            'location': {'name': 'Remote'},
            'absolute_url': 'https://example.com/jobs/2',
            'content': 'sell things',
        },
    ]
}


class CrawlGreenhouseTests(TestCase):
    def setUp(self):
        self.watched = WatchedCompany.objects.create(
            name='Fake Co', board_token='fakeco', keywords='engineer',
        )

    @patch('crawler.management.commands.crawl_greenhouse.requests.get')
    def test_upserts_matching_jobs_and_skips_others(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: FAKE_JOBS_RESPONSE)
        Command().crawl_company(self.watched)

        self.assertEqual(ScrapedJob.objects.count(), 1)
        job = ScrapedJob.objects.get()
        self.assertEqual(job.title, 'Backend Engineer')
        self.assertTrue(job.is_active)

    @patch('crawler.management.commands.crawl_greenhouse.requests.get')
    def test_jobs_missing_from_response_are_marked_inactive(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: FAKE_JOBS_RESPONSE)
        Command().crawl_company(self.watched)

        mock_get.return_value = Mock(status_code=200, json=lambda: {'jobs': []})
        Command().crawl_company(self.watched)

        job = ScrapedJob.objects.get()
        self.assertFalse(job.is_active)

    @patch('crawler.management.commands.crawl_greenhouse.requests.get')
    def test_non_200_response_is_skipped_without_error(self, mock_get):
        mock_get.return_value = Mock(status_code=404)
        Command().crawl_company(self.watched)
        self.assertEqual(ScrapedJob.objects.count(), 0)


class PromoteToLeadTests(TestCase):
    def test_promote_creates_lead_and_links_job(self):
        watched = WatchedCompany.objects.create(name='Fake Co', board_token='fakeco')
        job = ScrapedJob.objects.create(
            watched_company=watched, greenhouse_id=1, title='Backend Engineer',
            absolute_url='https://example.com/jobs/1',
        )

        modeladmin = Mock()
        promote_to_lead(modeladmin, Mock(), ScrapedJob.objects.filter(pk=job.pk))

        job.refresh_from_db()
        self.assertIsNotNone(job.promoted_lead)
        self.assertEqual(Lead.objects.count(), 1)

    def test_promote_skips_already_promoted_job(self):
        watched = WatchedCompany.objects.create(name='Fake Co', board_token='fakeco')
        job = ScrapedJob.objects.create(
            watched_company=watched, greenhouse_id=1, title='Backend Engineer',
            absolute_url='https://example.com/jobs/1',
        )
        modeladmin = Mock()
        promote_to_lead(modeladmin, Mock(), ScrapedJob.objects.filter(pk=job.pk))
        promote_to_lead(modeladmin, Mock(), ScrapedJob.objects.filter(pk=job.pk))

        self.assertEqual(Lead.objects.count(), 1)
