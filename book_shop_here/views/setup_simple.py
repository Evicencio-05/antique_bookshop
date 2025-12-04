from django.contrib.auth.models import User
from django.core.management import call_command
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

@csrf_exempt
@require_http_methods(["GET"])
def create_super_user_get(request):
    """
    Creates an initial superuser when accessed via GET.
    This should be removed after initial setup.
    """
    if not User.objects.filter(username='admin').exists():
        # Create superuser with initial credentials
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        # Try to run migrations if needed
        try:
            call_command('makemigrations', verbosity=0, interactive=False)
            call_command('migrate', verbosity=0, interactive=False)
        except Exception as e:
            # Ignore errors - migrations might already be applied
            pass
            
        # Return HTML response with success message
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Superuser Created</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .success { color: green; }
                .info { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1 class="success">Superuser Created Successfully!</h1>
            <div class="info">
                <h2>Login Details:</h2>
                <p><strong>Username:</strong> admin</p>
                <p><strong>Password:</strong> admin123</p>
                <p><a href="/admin/">Go to Admin Panel</a></p>
                <p><strong>Important:</strong> Remember to remove this endpoint after setup!</p>
            </div>
        </body>
        </html>
        """)
    
    # If superuser already exists
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Setup Already Complete</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .warning { color: orange; }
            .info { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1 class="warning">Setup Already Complete</h1>
        <div class="info">
            <p>A superuser already exists in the system.</p>
            <p><a href="/admin/">Go to Admin Panel</a></p>
            <p><a href="/">Go to Homepage</a></p>
        </div>
    </body>
    </html>
    """)