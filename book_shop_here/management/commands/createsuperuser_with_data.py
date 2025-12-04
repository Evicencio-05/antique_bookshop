from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from book_shop_here.models import Book, Author, Customer, Employee, Order

class Command(BaseCommand):
    help = 'Create a superuser with sample data for initial deployment'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Superuser username')
        parser.add_argument('--email', type=str, help='Superuser email')
        parser.add_argument('--password', type=str, help='Superuser password')

    def handle(self, *args, **options):
        username = options.get('username', 'admin')
        email = options.get('email', 'admin@example.com')
        password = options.get('password', 'admin123')
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING('User with this username already exists'))
            return
        
        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))