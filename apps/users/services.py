from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


class UserRegistrationService:
    """用戶註冊服務類"""
    
    # 錯誤代碼與訊息的映射
    ERROR_MESSAGES = {
        'username_format_invalid': '帳號只能包含英文字母和數字，不能有空格或特殊字元',
        'username_in_use': '此帳號已被註冊，請選擇其他帳號',
        'email_in_use': '此電子信箱已被註冊，請使用其他信箱',
        'password_format_invalid': '密碼只能包含英文字母和數字，不能有空格或特殊字元',
        'password_missing_uppercase': '密碼必須包含至少一個英文大寫字母',
        'password_missing_lowercase': '密碼必須包含至少一個英文小寫字母',
        'password_missing_number': '密碼必須包含至少一個數字',
        'password_mismatch': '兩次輸入的密碼不一致，請重新確認',
        'agree_terms_required': '請勾選同意服務條款'
    }
    
    @staticmethod
    def register_user(form):
        """
        註冊新用戶
        會return (success: bool, user: User|None, error_type: str|None)
        """
        if not form.is_valid():
            return False, None, 'validation_error'
        
        try:
            # 記錄註冊嘗試
            logger.info("Attempting user registration")
            user = form.save()
            logger.info(f"User registration successful: {user.username}")
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
        if error_type == 'database_error':
            messages.error(request, '註冊過程發生系統錯誤，請稍後再試。')
            return
        
        # 處理驗證錯誤
        if error_type == 'validation_error' and form:
            error_code = UserRegistrationService._get_form_error_code(form)
            message = UserRegistrationService.ERROR_MESSAGES.get(error_code)
            if message:
                messages.error(request, message)
                return
        
        # 預設訊息
        messages.error(request, '註冊失敗，請檢查您的輸入並重試。')
    
    @staticmethod
    def _get_form_error_code(form):
        """從表單錯誤中提取錯誤代碼"""
        if not hasattr(form, 'errors') or not form.errors:
            return None
        
        # Django 會將 ValidationError 轉換為字串，丟失 code 屬性
        # 我們需要根據錯誤訊息內容來判斷錯誤類型
        ERROR_MESSAGE_MAPPING = {
            'Invalid username format': 'username_format_invalid',
            'Username in use': 'username_in_use',
            'Email in use': 'email_in_use',
            'Invalid password format': 'password_format_invalid',
            'Missing uppercase': 'password_missing_uppercase',
            'Missing lowercase': 'password_missing_lowercase',
            'Missing number': 'password_missing_number',
            'Password mismatch': 'password_mismatch',
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
        
        # 處理沒有 code 的常見錯誤（如 agree_terms）
        FIELD_ERROR_MAPPING = {
            'agree_terms': 'agree_terms_required',
        }
        
        for field_name, field_errors in form.errors.items():
            if field_name in FIELD_ERROR_MAPPING and field_errors:
                return FIELD_ERROR_MAPPING[field_name]
        
        return None
    
    @staticmethod
    def _handle_validation_errors(request, form):
        """處理表單驗證錯誤"""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, str(error))
    
    
