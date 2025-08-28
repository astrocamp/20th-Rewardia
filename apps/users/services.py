from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


class UserRegistrationService:
    """用戶註冊服務類"""
    
    @staticmethod
    def register_user(form):
        """
        註冊新用戶
        會return (success: bool, user: User|None, error_type: str|None)
        """
        if not form.is_valid():
            return False, None, 'validation_error'
        
        try:
            user = form.save()
            return True, user, None
        except IntegrityError as e:
            logger.error(f"Database integrity error during user registration: {e}")
            return False, None, 'database_error'
    
    @staticmethod
    def handle_registration_success(request, user):
        """處理註冊成功"""
        messages.success(request, f'歡迎 {user.username}！註冊成功，請登入您的帳號。')
        

    
    @staticmethod
    def handle_registration_failure(request, error_type, form=None):
        """處理註冊失敗"""
        if error_type == 'validation_error':
            UserRegistrationService._handle_validation_errors(request, form)
        elif error_type == 'database_error':
            messages.error(request, '註冊過程發生系統錯誤，請稍後再試。')
        else:
            messages.error(request, '註冊失敗，請檢查您的輸入並重試。')
    
    @staticmethod
    def _handle_validation_errors(request, form):
        """處理表單驗證錯誤"""
        for field, errors in form.errors.items():
            for error in errors:
                error_code = getattr(error, 'code', None)
                if error_code == 'username_in_use':
                    messages.error(request, '此帳號已被註冊，請選擇其他帳號或嘗試登入。')
                elif error_code == 'email_in_use':
                    messages.error(request, '此電子信箱已被註冊，請使用其他信箱或嘗試登入。')
                else:
                    messages.error(request, error)
    
    @staticmethod
    def check_username_availability(username):
        """檢查帳號是否可用（不區分大小寫）"""
        return not User.objects.filter(username__iexact=username).exists()
    
    @staticmethod
    def check_email_availability(email):
        """檢查 email 是否可用（不區分大小寫）"""
        return not User.objects.filter(email__iexact=email).exists()
