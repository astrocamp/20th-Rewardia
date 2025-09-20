# Chatbot 工具函數
import logging
import functools

# 設定日誌記錄器
logger = logging.getLogger(__name__)


def handle_database_errors(default_return=None, log_error=True):
    """
    統一的資料庫錯誤處理裝飾器
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                return default_return if default_return is not None else []
        return wrapper
    return decorator


