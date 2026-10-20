from django.shortcuts import redirect, render

from . import services
from .models import Lead


def board_view(request):
    columns = services.leads_by_status()
    ordered_columns = [
        (status, label, columns[status]) for status, label in Lead.Status.choices
    ]
    return render(request, 'board/board.html', {'columns': ordered_columns})


def move_lead_view(request, lead_id):
    if request.method == 'POST':
        services.move_lead(lead_id, request.POST['status'])
    return redirect('board:board')
