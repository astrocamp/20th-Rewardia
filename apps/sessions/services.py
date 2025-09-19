import logging
from django.contrib import messages
from django.contrib.auth import login, logout

# 獲取 logger 實例
logger = logging.getLogger(__name__)

class UserAuthenticationService:
    """處理使用者登入、登出等身份驗證服務"""
    
    @staticmethod
    def login_user(request, form):
        """處理用戶登入邏輯"""
        if form.is_valid():
            user = form.get_user()
            return True, user, None
        else:
            error_code = UserAuthenticationService._get_form_error_code(form)
            return False, None, error_code

    @staticmethod
    def handle_login_success(request, user):
        """處理登入成功後的動作"""
        login(request, user)
        logger.info(f"User '{user.username}' logged in successfully.")
        messages.success(request, f'歡迎回來, {user.username}!')

    @staticmethod
    def handle_login_failure(request, error_type, form):
        """處理登入失敗後的動作"""
        username = form.cleaned_data.get('username', 'N/A')
        if error_type == 'invalid_login':
            logger.warning(f"Invalid login attempt for username: '{username}'.")
            messages.error(request, '帳號或密碼錯誤，請重新輸入。')
        elif error_type == 'inactive_user':
            logger.warning(f"Login attempt from inactive user: '{username}'.")
            messages.error(request, '此帳號已被停用，請聯繫管理員。')
        else:
            # 記錄未預期的表單錯誤
            logger.error(f"Unhandled login form error for '{username}'. Errors: {form.errors.as_json()}")
            messages.error(request, '發生未預期的錯誤，請稍後再試。')

    @staticmethod
    def logout_user(request):
        """處理用戶登出邏輯"""
        if request.user.is_authenticated:
            username = request.user.username
            logout(request)
            return username
        return None

    @staticmethod
    def handle_logout_success(request, username):
        """處理登出成功後的動作"""
        logger.info(f"User '{username}' logged out.")
        messages.success(request, f'使用者 {username} 已成功登出。')

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
