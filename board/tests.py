from django.test import TestCase
from django.urls import reverse

from . import services
from .models import Company, Lead


class ServicesTests(TestCase):
    def test_create_lead_gets_or_creates_company(self):
        lead = services.create_lead(company_name='Acme', role_title='Engineer')
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(lead.status, Lead.Status.NOT_STARTED)

        services.create_lead(company_name='Acme', role_title='Another Role')
        self.assertEqual(Company.objects.count(), 1)

    def test_move_lead_updates_status(self):
        lead = services.create_lead(company_name='Acme', role_title='Engineer')
        moved = services.move_lead(lead.id, Lead.Status.APPLIED)
        self.assertEqual(moved.status, Lead.Status.APPLIED)

    def test_move_lead_rejects_invalid_status(self):
        lead = services.create_lead(company_name='Acme', role_title='Engineer')
        with self.assertRaises(ValueError):
            services.move_lead(lead.id, 'NOT_A_REAL_STATUS')

    def test_leads_by_status_buckets_by_status(self):
        services.create_lead(company_name='Acme', role_title='Engineer')
        columns = services.leads_by_status()
        self.assertEqual(len(columns[Lead.Status.NOT_STARTED]), 1)
        self.assertEqual(len(columns[Lead.Status.APPLIED]), 0)


class BoardViewTests(TestCase):
    def test_board_view_renders(self):
        services.create_lead(company_name='Acme', role_title='Engineer')
        response = self.client.get(reverse('board:board'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Engineer')

    def test_move_lead_view_updates_status(self):
        lead = services.create_lead(company_name='Acme', role_title='Engineer')
        response = self.client.post(
            reverse('board:move_lead', args=[lead.id]), {'status': Lead.Status.APPLIED}
        )
        self.assertEqual(response.status_code, 302)
        lead.refresh_from_db()
        self.assertEqual(lead.status, Lead.Status.APPLIED)


class LeadApiTests(TestCase):
    def test_create_and_move_via_api(self):
        company = Company.objects.create(name='Acme')
        response = self.client.post(
            '/api/leads/', {'company': company.id, 'role_title': 'Engineer'}
        )
        self.assertEqual(response.status_code, 201)
        lead_id = response.json()['id']

        response = self.client.post(
            f'/api/leads/{lead_id}/move/', {'status': Lead.Status.APPLIED}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], Lead.Status.APPLIED)
