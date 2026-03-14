from django.db import models
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from leads.models import LeadTransfer
from leads.serializers import LeadTransferSerializer


class LeadTransferViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Read-only viewset for transfer history.

    Nested route:
        GET /leads/{lead_pk}/transfers/   – transfers for one lead

    Top-level route:
        GET /leads/transfers/?user_id=<uuid>  – transfers involving a user
    """
    serializer_class = LeadTransferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Nested: /leads/{lead_pk}/transfers/
        lead_pk = self.kwargs.get('lead_pk')
        if lead_pk:
            return (
                LeadTransfer.objects
                .filter(lead_id=lead_pk)
                .select_related('from_user', 'to_user', 'transferred_by')
                .order_by('created_at')
            )

        # Top-level: ?user_id=<uuid>
        user_id = self.request.query_params.get('user_id')
        qs = LeadTransfer.objects.select_related('from_user', 'to_user', 'transferred_by', 'lead')
        if user_id:
            qs = qs.filter(
                models.Q(from_user_id=user_id) | models.Q(to_user_id=user_id)
            )
        return qs.order_by('-created_at')

