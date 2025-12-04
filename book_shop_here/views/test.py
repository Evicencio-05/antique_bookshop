from django.http import HttpResponse

def simple_test(request):
    """
    Simple test endpoint to verify the application is working
    """
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Application Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1 class="success">Application is Working!</h1>
        <p>Your Django application is running correctly.</p>
        <p><a href="/">Go to Homepage</a></p>
    </body>
    </html>
    """)