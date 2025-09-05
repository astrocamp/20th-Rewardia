from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import google.generativeai as genai
from .services import ChatbotDataService, ChatbotResponseBuilder

# Configure the Gemini API with the key from Django settings
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError:
    pass


@csrf_exempt
def chat_api(request):
    """
    AI 助理 API 端點，整合知識庫和資料庫查詢功能
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

            # 建構包含資料庫資訊的上下文提示詞
            context_prompt = ChatbotResponseBuilder.build_context_prompt(message, request.user)
            
            # 組合完整的提示詞
            full_prompt = f"{context_prompt}\n\n## 用戶問題\n{message}\n\n請根據以上資訊回答用戶的問題："

            # --- Call Gemini API ---
            model = genai.GenerativeModel('gemini-2.0-flash')
            gemini_response = model.generate_content(full_prompt)
            response_message = gemini_response.text
            
            # 驗證 Gemini 回應是否包含虛假的卡片名稱
            validated_response = ChatbotResponseBuilder.validate_response(
                response_message, message, request.user
            )
            
            # 根據用戶問題增強回應內容
            enhanced_response = ChatbotResponseBuilder.enhance_response_with_data(
                validated_response, message, request.user
            )
            # -----------------------

            return JsonResponse({'response': enhanced_response})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            # Catch potential errors from the Gemini API call and return a generic error
            return JsonResponse({'error': f'An error occurred while communicating with the AI service.'}, status=500)

    # If the request method is not POST, return an error
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
