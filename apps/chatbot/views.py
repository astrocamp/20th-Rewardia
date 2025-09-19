from django.http import JsonResponse
from asgiref.sync import sync_to_async
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
import json
import logging
import google.generativeai as genai
from .intent_analyzer import ChatbotResponseBuilder

# 設定日誌記錄器
logger = logging.getLogger(__name__)

# Configure the Gemini API with the key from Django settings
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError:
    pass

def get_gemini_response_sync(prompt):
    """
    A synchronous wrapper for the Gemini API call to isolate it from the async context.
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API call failed: {str(e)}")
        raise

def build_full_prompt(context_prompt, message):
    """
    組合完整的提示詞
    """
    return f"{context_prompt}\n\n## 用戶問題\n{message}\n\n請根據以上資訊回答用戶的問題："

@csrf_protect
@require_http_methods(["POST"])
async def chat_api(request):
    """
    AI 助理 API 端點
    """
    if request.method == 'POST':
        # Check if the API key is configured
        if not settings.GEMINI_API_KEY:
            logger.error("Gemini API key not configured")
            return JsonResponse({'error': 'Gemini API 金鑰未配置'}, status=500)

        try:
            # Parse request data
            body = request.body
            data = json.loads(body)
            message = data.get('message')
            current_page = data.get('current_page', '')  # 獲取當前頁面信息

            if not message:
                return JsonResponse({'error': '訊息內容為必填'}, status=400)

            # Get user_id if authenticated (using sync_to_async to handle async context)
            def get_user_id_sync():
                return request.user.id if request.user.is_authenticated else None
            
            user_id = await sync_to_async(get_user_id_sync, thread_sensitive=False)()
            
            # Get conversation history
            conversation_history = data.get('conversation_history', [])

            # 1. Asynchronously analyze user intent with conversation history
            intent = await sync_to_async(ChatbotResponseBuilder.analyze_user_intent, thread_sensitive=True)(message, conversation_history)

            # 2. Asynchronously build context prompt with conversation history
            context_prompt = await sync_to_async(ChatbotResponseBuilder.build_context_prompt_with_history, thread_sensitive=True)(intent, user_id, conversation_history)
            
            # 3. Build full prompt
            full_prompt = build_full_prompt(context_prompt, message)

            # 4. Call Gemini API
            response_message = await sync_to_async(get_gemini_response_sync, thread_sensitive=False)(full_prompt)
            
            # 5. Validate response
            validated_response = await sync_to_async(ChatbotResponseBuilder.validate_response, thread_sensitive=True)(
                response_message, message, user_id
            )
            
            # 6. Enhance response
            enhanced_response = await sync_to_async(ChatbotResponseBuilder.enhance_response_with_data, thread_sensitive=True)(
                validated_response, intent, user_id, current_page
            )

            return JsonResponse({'response': enhanced_response})

        except json.JSONDecodeError:
            logger.warning("Invalid JSON format in chatbot request")
            return JsonResponse({'error': '無效的 JSON 格式'}, status=400)
        except Exception as e:
            logger.error(f"Chatbot API Error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'AI 服務暫時無法使用，請稍後再試'}, status=500)

    # If the request method is not POST, return an error
    return JsonResponse({'error': '只允許 POST 方法'}, status=405)
