from rest_framework import viewsets, mixins, permissions
from rest_framework.generics import get_object_or_404
from leads.models import Lead, LeadNote
from leads.serializers import LeadNoteSerializer


class LeadNoteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET  /leads/{lead_pk}/notes/         — list notes (newest first)
    POST /leads/{lead_pk}/notes/         — create a new note

    Notes are immutable: no PUT / PATCH / DELETE actions are exposed.
    """
    serializer_class = LeadNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_lead(self):
        return get_object_or_404(Lead, pk=self.kwargs['lead_pk'])

    def get_queryset(self):
        lead = self._get_lead()
        return LeadNote.objects.filter(lead=lead).order_by('-created_at')

    def perform_create(self, serializer):
        lead = self._get_lead()
        serializer.save(lead=lead)
