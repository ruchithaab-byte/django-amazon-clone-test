import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(project_root))

# Configure Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'DjangoEcommerceApp.settings'

def pytest_configure():
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_TZ=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sites',
                'DjangoEcommerceApp',
            ],
            SECRET_KEY='test_secret_key',
            MIGRATION_MODULES={'DjangoEcommerceApp': 'DjangoEcommerceApp.migrations'},
        )
        django.setup()

        from django.core.management import call_command
        from django.apps import apps

        # Create tables
        call_command('migrate', verbosity=0, interactive=False)