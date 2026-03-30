from django.core.cache import cache
from rest_framework import serializers
from leads.models import Lead, LeadStage
from leads.serializers.lead_note import LeadNoteSerializer
from leads.serializers.lead_transfer import LeadTransferSerializer
from projects.models import Project
from authentication.models import User


# ── Nested helpers ───────────────────────────────────────────────────

class StageSerializer(serializers.ModelSerializer):
    """Minimal stage representation used inside a lead."""
    class Meta:
        model = LeadStage
        fields = ['id', 'name', 'order', 'is_default']


class ProjectSummarySerializer(serializers.ModelSerializer):
    """Compact project info shown on the lead detail card."""
    class Meta:
        model = Project
        fields = ['id', 'name', 'address', 'type', 'size', 'size_unit', 'image']


class AssignedUserSerializer(serializers.ModelSerializer):
    """Compact user info shown on lead cards."""
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']


# ── Lead serializers ─────────────────────────────────────────────────

class LeadListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views (is_detailed=false)."""
    stage = StageSerializer(read_only=True)
    project = ProjectSummarySerializer(read_only=True)
    latest_note = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = ['id', 'full_name', 'email', 'phone', 'job_title', 'stage', 'project', 'latest_note']

    def get_latest_note(self, obj):
        # Use prefetched_notes if available (set by LeadViewSet queryset)
        # to avoid an extra DB query per lead (N+1)
        prefetched = getattr(obj, 'prefetched_notes', None)
        if prefetched is not None:
            note = prefetched[0] if prefetched else None
        else:
            note = obj.notes.order_by('-created_at').first()
        return LeadNoteSerializer(note).data if note else None


class LeadDetailSerializer(serializers.ModelSerializer):
    """
    Full lead detail serializer.

    - `stage`            – nested current stage object
    - `pipeline_stages`  – all stages ordered by `order`
    - `project`          – nested associated project
    - `notes`            – list of LeadNote objects (newest first, immutable)
    - `transfer_history` – chronological list of LeadTransfer records
    """
    stage = StageSerializer(read_only=True)
    pipeline_stages = serializers.SerializerMethodField()
    project = ProjectSummarySerializer(read_only=True)
    notes = serializers.SerializerMethodField()
    transfer_history = serializers.SerializerMethodField()
    min_budget = serializers.DecimalField(
        max_digits=15, decimal_places=2,
        coerce_to_string=False, allow_null=True, required=False,
    )
    max_budget = serializers.DecimalField(
        max_digits=15, decimal_places=2,
        coerce_to_string=False, allow_null=True, required=False,
    )

    class Meta:
        model = Lead
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'job_title',
            'min_budget',
            'max_budget',
            'stage',
            'pipeline_stages',
            'notes',
            'transfer_history',
            'project',
            'form_id',
            'assigned_to',
            'custom_data',
            'created_time',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'pipeline_stages', 'notes', 'transfer_history', 'created_at', 'updated_at', 'created_time', 'custom_data']

    def get_pipeline_stages(self, obj):
        # Cache stages for 5 minutes — they almost never change
        cached = cache.get('pipeline_stages')
        if cached is None:
            stages = LeadStage.objects.order_by('order', 'name')
            cached = StageSerializer(stages, many=True).data
            cache.set('pipeline_stages', cached, timeout=300)
        return cached

    def get_notes(self, obj):
        notes = obj.notes.order_by('-created_at')
        return LeadNoteSerializer(notes, many=True).data

    def get_transfer_history(self, obj):
        transfers = obj.transfers.select_related(
            'from_user', 'to_user', 'transferred_by'
        ).order_by('created_at')
        return LeadTransferSerializer(transfers, many=True).data

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['assigned_to'] = AssignedUserSerializer(instance.assigned_to).data if instance.assigned_to else None
        return rep


class LeadSerializer(serializers.ModelSerializer):
    """
    Full serializer for lead create / update operations.

    Write:  send `stage` and `project` as plain UUIDs.
    Read:   `stage` and `project` are returned as nested objects.
    """
    latest_note = serializers.SerializerMethodField()
    stage = serializers.PrimaryKeyRelatedField(
        queryset=LeadStage.objects.all(),
        allow_null=True,
        required=False,
    )
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        allow_null=True,
        required=False,
    )
    min_budget = serializers.DecimalField(
        max_digits=15, decimal_places=2,
        coerce_to_string=False, allow_null=True, required=False,
    )
    max_budget = serializers.DecimalField(
        max_digits=15, decimal_places=2,
        coerce_to_string=False, allow_null=True, required=False,
    )

    class Meta:
        model = Lead
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'job_title',
            'min_budget',
            'max_budget',
            'stage',
            'project',
            'form_id',
            'assigned_to',
            'latest_note',
            'created_time',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_time']

    def get_latest_note(self, obj):
        # Use prefetched_notes if available (set by LeadViewSet queryset)
        # to avoid an extra DB query per lead (N+1)
        prefetched = getattr(obj, 'prefetched_notes', None)
        if prefetched is not None:
            note = prefetched[0] if prefetched else None
        else:
            note = obj.notes.order_by('-created_at').first()
        return LeadNoteSerializer(note).data if note else None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['stage'] = StageSerializer(instance.stage).data if instance.stage else None
        rep['project'] = ProjectSummarySerializer(instance.project).data if instance.project else None
        rep['assigned_to'] = AssignedUserSerializer(instance.assigned_to).data if instance.assigned_to else None
        return rep
