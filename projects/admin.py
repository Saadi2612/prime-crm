from django.contrib import admin
from projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'form_id', 'size', 'size_unit', 'created_at']
    list_filter = ['size_unit', 'created_at']
    search_fields = ['name', 'address', 'form_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
