from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Company, Lead
from .serializers import CompanySerializer, LeadSerializer, MoveLeadSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.select_related('company').all()
    serializer_class = LeadSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        serializer = MoveLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = services.move_lead(pk, serializer.validated_data['status'])
        return Response(LeadSerializer(lead).data)
