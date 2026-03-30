from django.db import models
from prime_crm.utils import UUIDTimestampedModel


class LeadStage(UUIDTimestampedModel):
    """
    A pipeline stage that a Lead can be in.
    Admins/managers can add, edit, or delete stages.
    The default stages are seeded via a data migration and carry is_default=True.
    stage_type encodes the *semantic meaning* of a stage independently of its name,
    so stats queries remain correct even if names are changed.
    """

    class StageType(models.TextChoices):
        QUALIFIED   = 'qualified',   'Qualified'    # deal won / closed successfully
        UNQUALIFIED = 'unqualified', 'Unqualified'  # deal lost / closed unsuccessfully
        DEFAULT     = 'default',     'Default'      # any active in-progress stage

    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order (ascending).")
    is_default = models.BooleanField(
        default=False,
        help_text="True for the built-in default stages.",
    )
    stage_type = models.CharField(
        max_length=20,
        choices=StageType.choices,
        default=StageType.DEFAULT,
        help_text="Semantic type of the stage — independent of the display name.",
    )

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
