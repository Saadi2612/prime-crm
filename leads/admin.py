from django.contrib import admin
from .models import Lead, LeadNote, LeadTransfer

# Register your models here.
admin.site.register(Lead)
admin.site.register(LeadNote)
admin.site.register(LeadTransfer)

