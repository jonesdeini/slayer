from rest_framework import serializers

from .models import Company, Lead


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'website', 'notes', 'created_at', 'updated_at']


class LeadSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'company', 'company_name', 'role_title', 'status',
            'job_url', 'notes', 'applied_at', 'created_at', 'updated_at',
        ]


class MoveLeadSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Lead.Status.choices)
