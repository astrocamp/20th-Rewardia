import logging
from django.contrib import messages
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class UserRegistrationService:
    """處理使用者註冊相關服務"""

    @staticmethod
    def register_user(form):
        """處理用戶註冊邏輯"""
        if form.is_valid():
            user = form.save()
            return True, user, None
        else:
            error_code = UserRegistrationService._get_form_error_code(form)
            return False, None, error_code

    @staticmethod
    def handle_registration_success(request, user):
        """處理註冊成功後的動作"""
        logger.info(f"New user '{user.username}' registered successfully.")
        messages.success(request, f'使用者 {user.username} 註冊成功！請登入。')

    @staticmethod
    def handle_registration_failure(request, error_type, form):
        """處理註冊失敗後的動作"""
        username = form.cleaned_data.get('username', 'N/A')
        logger.warning(f"User registration failed for '{username}'. Error code: {error_type}, Errors: {form.errors.as_json()}")
        
        error_messages = {
            'username_format_invalid': '帳號格式不符，請使用英數字組合。',
            'username_in_use': '此帳號已被註冊，請更換一個。',
            'email_in_use': '此電子信箱已被註冊。',
            'password_format_invalid': '密碼格式不符，請使用英數字組合。',
            'password_missing_uppercase': '密碼需包含至少一個大寫字母。',
            'password_missing_lowercase': '密碼需包含至少一個小寫字母。',
            'password_missing_number': '密碼需包含至少一個數字。',
            'password_mismatch': '兩次輸入的密碼不一致。',
            'required': '請勾選同意服務條款'
        }
        
        message = error_messages.get(error_type, '註冊失敗，請檢查您輸入的資料。')
        messages.error(request, message)

    @staticmethod
    def check_username_availability(username):
        """檢查帳號是否可用"""
        return not User.objects.filter(username=username).exists()

    @staticmethod
    def check_email_availability(email):
        """檢查電子信箱是否可用"""
        return not User.objects.filter(email=email).exists()

    @staticmethod
    def _get_form_error_code(form):
        """從表單錯誤中提取錯誤代碼"""
        if not hasattr(form, 'errors') or not form.errors:
            return None
        errors_data = form.errors.as_data()
        for field, error_list in errors_data.items():
            for error in error_list:
                if hasattr(error, 'code') and error.code:
                    return error.code
        return None

    
    
