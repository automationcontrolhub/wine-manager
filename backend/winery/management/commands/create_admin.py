from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Crea un superuser admin di default se non esiste'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@winery.local', 'admin')
            self.stdout.write(self.style.SUCCESS('Superuser "admin" creato (password: admin)'))
        else:
            self.stdout.write(self.style.WARNING('Superuser "admin" esiste già'))
