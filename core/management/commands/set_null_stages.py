from django.core.management.base import BaseCommand
from leads.models import Lead, LeadStage

class Command(BaseCommand):
    help = 'Sets the stage of all leads with stage as null to the one with order == 1.'

    def handle(self, *args, **kwargs):
        target_stage = LeadStage.objects.filter(order=1).first()
        
        if not target_stage:
            self.stdout.write(self.style.ERROR('LeadStage with order 1 does not exist.'))
            return
            
        leads_to_update = Lead.objects.filter(stage__isnull=True)
        count = leads_to_update.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No leads found with a null stage.'))
            return

        # Using update() for bulk operation which is much faster than saving individually
        leads_to_update.update(stage=target_stage)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} leads, setting their stage to "{target_stage.name}".'))
