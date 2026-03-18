from rest_framework import serializers
from leads.models import LeadNote


class LeadNoteSerializer(serializers.ModelSerializer):
    """
    Serialiser for LeadNote.

    On CREATE: only `body` is writable; `lead` is injected from the URL.
    Read-only fields ensure notes cannot be modified after creation.
    """

    class Meta:
        model = LeadNote
        fields = ['id', 'body', 'next_follow_up', 'created_at']
        read_only_fields = ['id', 'created_at']
