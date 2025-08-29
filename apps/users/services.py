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
                messages.error(request, str(error))
    
    
