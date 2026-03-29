from django.contrib import admin
from .models import Lead, LeadNote, LeadTransfer, LeadStage

# Register your models here.
admin.site.register(Lead)
admin.site.register(LeadNote)
admin.site.register(LeadTransfer)
admin.site.register(LeadStage)

