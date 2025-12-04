from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.management import call_command
from django.http import JsonResponse
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

@require_http_methods(["POST"])
@csrf_exempt
def create_initial_superuser(request):
    """
    Creates an initial superuser with hardcoded credentials.
    This URL should be removed after initial setup.
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
        except:
            pass  # Migrations might already be applied

        # Log in the user
        user = User.objects.get(username="admin")
        login(request, user)

        return JsonResponse(
            {"status": "success", "message": "Superuser created successfully and logged in"}
        )

    return JsonResponse({"status": "error", "message": "Superuser already exists"})
