"""
The one logic layer for the board app.

DRF viewsets and the plain Django views both call into this module rather
than querying/mutating Lead and Company directly — keeps the kanban board
and the API from drifting into two implementations of the same logic.
"""

from django.shortcuts import get_object_or_404

from .models import Company, Lead


def leads_by_status():
    """Return an ordered dict of status -> leads, for rendering kanban columns."""
    leads = Lead.objects.select_related('company').all()
    columns = {status: [] for status, _label in Lead.Status.choices}
    for lead in leads:
        columns[lead.status].append(lead)
    return columns


def move_lead(lead_id, new_status):
    if new_status not in Lead.Status.values:
        raise ValueError(f'invalid status: {new_status}')
    lead = get_object_or_404(Lead, pk=lead_id)
    lead.status = new_status
    lead.save(update_fields=['status', 'updated_at'])
    return lead


def create_lead(*, company_name, role_title, job_url='', notes='', status=Lead.Status.NOT_STARTED):
    company, _created = Company.objects.get_or_create(name=company_name)
    return Lead.objects.create(
        company=company,
        role_title=role_title,
        job_url=job_url,
        notes=notes,
        status=status,
    )
