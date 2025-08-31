from django.contrib import messages
from django.contrib.auth import login as django_login, logout
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class UserAuthenticationService:
    """用戶認證服務類"""
    
    # 錯誤代碼與訊息的映射
    ERROR_MESSAGES = {
        'invalid_login': '帳號或密碼錯誤，請重新輸入。',
        'inactive_user': '此帳號已被停用，請聯繫管理員。'
    }
    
    @staticmethod
    def login_user(request, form):
        """
        用戶登入處理
        會 return (success: bool, user: User|None, error_type: str|None)
        """
        if not form.is_valid():
            return False, None, 'validation_error'
        
        try:
            # 記錄認證嘗試
            logger.info("Attempting user authentication")
            user = form.get_user()
            logger.info(f"Authentication result: {'success' if user else 'failed'}")
            
            # 記錄登入嘗試
            logger.info(f"Attempting login for user: {user.username}")
            django_login(request, user)
            logger.info(f"Login successful for user: {user.username}")
                        
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])            
            request.session.set_expiry(0)
            
            return True, user, None

            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, None, 'system_error'
    
    @staticmethod
    def handle_login_success(request, user):
        """處理登入成功"""
        messages.success(request, f'歡迎回來，{user.username}！')
    
    @staticmethod
    def handle_login_failure(request, error_type, form=None):
        """處理登入失敗"""
        if error_type == 'system_error':
            messages.error(request, '登入過程發生系統錯誤，請稍後再試。')
            return
        
        # 處理驗證錯誤
        if error_type == 'validation_error' and form:
            error_code = UserAuthenticationService._get_form_error_code(form)
            message = UserAuthenticationService.ERROR_MESSAGES.get(error_code)
            if message:
                messages.error(request, message)
                return
        
        # 預設訊息
        messages.error(request, '登入失敗，請檢查您的輸入並重試。')
    
    @staticmethod
    def _get_form_error_code(form):
        """從表單錯誤中提取錯誤代碼"""
        if not hasattr(form, 'errors') or not form.errors:
            return None
        
        # Django 會將 ValidationError 轉換為字串，丟失 code 屬性
        # 我們需要根據錯誤訊息內容來判斷錯誤類型
        ERROR_MESSAGE_MAPPING = {
            'Invalid login': 'invalid_login',
            'Inactive user': 'inactive_user',
        }
        
        # 檢查非欄位錯誤（來自 clean() 方法）
        if '__all__' in form.errors:
            for error_msg in form.errors['__all__']:
                error_str = str(error_msg)
                if error_str in ERROR_MESSAGE_MAPPING:
                    return ERROR_MESSAGE_MAPPING[error_str]
        
        # 檢查欄位錯誤
        for field_name, field_errors in form.errors.items():
            if field_name == '__all__':
                continue
            for error_msg in field_errors:
                error_str = str(error_msg)
                if error_str in ERROR_MESSAGE_MAPPING:
                    return ERROR_MESSAGE_MAPPING[error_str]
        
        return None
    
    @staticmethod
    def logout_user(request):
        """用戶登出處理"""
        if request.user.is_authenticated:
            username = request.user.username
            logout(request)
            return username
        return None
    
    @staticmethod
    def handle_logout_success(request, username):
        """處理登出成功"""
        messages.success(request, f'{username}，您已成功登出。')