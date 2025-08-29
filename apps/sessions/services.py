from django.contrib import messages
from django.contrib.auth import login as django_login, logout
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class UserAuthenticationService:
    """用戶認證服務類"""
    
    @staticmethod
    def login_user(request, form):
        """
        用戶登入處理
        會 return (success: bool, user: User|None, error_type: str|None)
        """
        if not form.is_valid():
            return False, None, 'validation_error'
        
        try:
            user = form.get_user()
            
            # 執行登入
            django_login(request, user)
            
            # 更新最後登入時間
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # 設定會話期限為瀏覽器關閉時過期
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
        if error_type == 'validation_error':
            UserAuthenticationService._handle_validation_errors(request, form)
        elif error_type == 'system_error':
            messages.error(request, '登入過程發生系統錯誤，請稍後再試。')
        else:
            messages.error(request, '登入失敗，請檢查您的輸入並重試。')
    
    @staticmethod
    def _handle_validation_errors(request, form):
        """處理表單驗證錯誤"""
        for field, errors in form.errors.items():
            for error in errors:
                error_code = getattr(error, 'code', None)
                if error_code == 'invalid_login':
                    messages.error(request, '帳號或密碼錯誤，請重新輸入。')
                elif error_code == 'inactive_user':
                    messages.error(request, '此帳號已被停用，請聯繫管理員。')
                else:
                    messages.error(request, str(error))
    
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