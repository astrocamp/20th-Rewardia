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
    AI 助理 API 端點
    """
    if request.method == 'POST':
        # Check if the API key is configured
        if not settings.GEMINI_API_KEY:
            return JsonResponse({'error': 'Gemini API 金鑰未配置'}, status=500)

        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            message = data.get('message')

            if not message:
                return JsonResponse({'error': '訊息內容為必填'}, status=400)

            # 1. 分析使用者意圖
            intent = ChatbotResponseBuilder.analyze_user_intent(message)

            # 2. 根據意圖建構上下文提示詞
            context_prompt = ChatbotResponseBuilder.build_context_prompt(intent, request.user)
            
            # 組合完整的提示詞
            full_prompt = f"{context_prompt}\n\n## 用戶問題\n{message}\n\n請根據以上資訊回答用戶的問題："

            # 3. 呼叫 Gemini API
            model = genai.GenerativeModel('gemini-2.0-flash')
            gemini_response = model.generate_content(full_prompt)
            response_message = gemini_response.text
            
            # 4. 驗證回應
            validated_response = ChatbotResponseBuilder.validate_response(
                response_message, message, request.user
            )
            
            # 5. 根據意圖增強回應
            enhanced_response = ChatbotResponseBuilder.enhance_response_with_data(
                validated_response, intent, request.user
            )

            return JsonResponse({'response': enhanced_response})

        except json.JSONDecodeError:
            return JsonResponse({'error': '無效的 JSON 格式'}, status=400)
        except Exception as e:
            # Catch potential errors from the Gemini API call and return a generic error
            return JsonResponse({'error': 'AI 服務暫時無法使用，請稍後再試'}, status=500)

    # If the request method is not POST, return an error
    return JsonResponse({'error': '只允許 POST 方法'}, status=405)
