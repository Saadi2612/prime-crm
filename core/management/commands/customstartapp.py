import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates a Django app with custom folder structure'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='Name of the app to create')

    def handle(self, *args, **options):
        app_name = options['app_name']
        
        # Define your custom folder structure
        structure = {
            app_name: {
                'migrations': {
                    '__init__.py': '',
                },
                'models': {
                    '__init__.py': '',
                },
                'serializers': {
                    '__init__.py': '',
                },
                'views': {
                    '__init__.py': '',
                },
                '__init__.py': '',
                'admin.py': self.get_admin_template(),
                'apps.py': self.get_apps_template(app_name),
                'tests.py': self.get_tests_template(),
                'urls.py': self.get_urls_template(app_name),
                'utils.py': self.get_utils_template(),
            }
        }
        
        # Create the structure
        self.create_structure(structure)
        self.stdout.write(self.style.SUCCESS(f'Successfully created app "{app_name}" with custom structure'))

    def create_structure(self, structure, base_path=''):
        """Recursively create folders and files"""
        for name, content in structure.items():
            path = os.path.join(base_path, name)
            
            if isinstance(content, dict):
                # It's a directory
                os.makedirs(path, exist_ok=True)
                self.create_structure(content, path)
            else:
                # It's a file
                with open(path, 'w') as f:
                    f.write(content)

    def get_apps_template(self, app_name):
        """Generate apps.py content"""
        class_name = ''.join(word.capitalize() for word in app_name.split('_'))
        return f"""from django.apps import AppConfig


class {class_name}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name}'
"""

    def get_admin_template(self):
        """Generate admin.py content"""
        return """from django.contrib import admin

# Register your models here.
"""

    def get_tests_template(self):
        """Generate tests.py content"""
        return """from django.test import TestCase

# Create your tests here.
"""

    def get_urls_template(self, app_name):
        """Generate urls.py content"""
        return f"""from django.urls import path
from . import views

app_name = '{app_name}'

urlpatterns = [
    # Add your URL patterns here
]
"""

    def get_utils_template(self):
        """Generate utils.py content"""
        return """# Utility functions for this app
"""