import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from django.contrib.auth.models import User

# Create superuser if it doesn't exist
if not User.objects.filter(username='Kat').exists():
    User.objects.create_superuser('Kat', 'catriel@hf.cx', 'admin13')
    print('✓ Superuser "Kat" created successfully')
else:
    print('ℹ Superuser "Kat" already exists')
