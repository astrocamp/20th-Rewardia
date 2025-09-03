from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import google.generativeai as genai

# Configure the Gemini API with the key from Django settings
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError:
    # This prevents the app from crashing if the key is missing on startup.
    # The view itself will handle the error gracefully.
    pass


@csrf_exempt
def chat_api(request):
    """
    API endpoint to handle chat requests.
    """
    if request.method == 'POST':
        # Check if the API key is configured
        if not settings.GEMINI_API_KEY:
            return JsonResponse({'error': 'The Gemini API key is not configured on the server.'}, status=500)

        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            message = data.get('message')

            if not message:
                return JsonResponse({'error': 'Message is required'}, status=400)

            # --- Call Gemini API ---
            model = genai.GenerativeModel('gemini-pro')
            gemini_response = model.generate_content(message)
            response_message = gemini_response.text
            # -----------------------

            return JsonResponse({'response': response_message})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            # Catch potential errors from the Gemini API call and return a generic error
            return JsonResponse({'error': f'An error occurred while communicating with the AI service.'}, status=500)

    # If the request method is not POST, return an error
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
