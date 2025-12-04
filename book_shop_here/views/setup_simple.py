from django.contrib.auth.models import User
from django.core.management import call_command
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["GET"])
def create_super_user_get(request):
    import traceback
    
    try:
        """
        Creates an initial superuser when accessed via GET.
        This should be removed after initial setup.
        """
        if not User.objects.filter(username="admin").exists():
            # Create superuser with initial credentials
            User.objects.create_superuser(
                username="admin", email="admin@example.com", password="admin123"
        )

        # Try to run migrations if needed
        try:
            call_command("makemigrations", verbosity=0, interactive=False)
            call_command("migrate", verbosity=0, interactive=False)
        except Exception:
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
                .error { background: #ffebee; padding: 10px; margin: 10px 0; border-radius: 5px; color: #b71c1c; }
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
    
    except Exception as e:
        error_details = traceback.format_exc()
        return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Setup Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .error {{ background: #ffebee; padding: 10px; margin: 10px 0; border-radius: 5px; color: #b71c1c; }}
                pre {{ background: #f5f5f5; padding: 10px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1 class="error">Error During Setup</h1>
            <p>The following error occurred while trying to create a superuser:</p>
            <div class="error">
                <strong>Error:</strong> {{str(e)}}
            </div>
            <p><strong>Traceback:</strong></p>
            <pre>{error_details}</pre>
        </body>
        </html>
        """
        )
