from django.urls import path

from . import views

app_name = 'board'

urlpatterns = [
    path('', views.board_view, name='board'),
    path('leads/<int:lead_id>/move/', views.move_lead_view, name='move_lead'),
]
