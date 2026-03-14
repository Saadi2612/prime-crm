from rest_framework import serializers
from leads.models import LeadTransfer


class TransferUserSerializer(serializers.Serializer):
    """Compact user representation inside a transfer record."""
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    email = serializers.EmailField()


class LeadTransferSerializer(serializers.ModelSerializer):
    from_user = TransferUserSerializer(read_only=True)
    to_user = TransferUserSerializer(read_only=True)
    transferred_by = TransferUserSerializer(read_only=True)

    class Meta:
        model = LeadTransfer
        fields = [
            'id',
            'lead',
            'from_user',
            'to_user',
            'transferred_by',
            'note',
            'created_at',
        ]
        read_only_fields = fields
