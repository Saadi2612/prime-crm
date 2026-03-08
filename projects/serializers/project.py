from rest_framework import serializers
from projects.models import Project


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer used when is_detailed=false."""
    size = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = Project
        fields = ['id', 'name', 'type', 'size', 'size_unit']


class ProjectSerializer(serializers.ModelSerializer):
    """Full serializer used when is_detailed=true (default)."""
    size = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'address',
            'type',
            'form_id',
            'image',
            'size',
            'size_unit',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
