"""
BIN 快取服務
用於快取信用卡 BIN 碼對應的銀行資訊，避免重複查詢外部 API
"""
import json
import os
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class BINCacheService:
    """BIN 碼快取服務類別"""
    
    def __init__(self):
        # 快取檔案路徑：放在專案根目錄的 data 資料夾
        self.cache_file = os.path.join(settings.BASE_DIR, 'data', 'bin_cache.json')
        self.cache = self.load_cache()
    
    def load_cache(self) -> Dict[str, Any]:
        """載入快取資料"""
        try:
            # 確保 data 目錄存在
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    logger.info(f"成功載入 BIN 快取，共 {len(cache_data)} 筆記錄")
                    return cache_data
            else:
                logger.info("BIN 快取檔案不存在，建立新的空快取")
                return {}
        except Exception as e:
            logger.error(f"載入 BIN 快取失敗: {e}")
            return {}
    
    def save_cache(self) -> bool:
        """儲存快取資料"""
        try:
            # 確保 data 目錄存在
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功儲存 BIN 快取，共 {len(self.cache)} 筆記錄")
            return True
        except Exception as e:
            logger.error(f"儲存 BIN 快取失敗: {e}")
            return False
    
    def get_bank_by_bin(self, bin_code: str) -> Optional[Dict[str, Any]]:
        """
        根據 BIN 碼取得銀行資訊
        
        Args:
            bin_code: 信用卡前6碼
            
        Returns:
            銀行資訊字典，包含 bank, card, type 等資訊，如果找不到則返回 None
        """
        if not bin_code or len(bin_code) != 6:
            logger.warning(f"無效的 BIN 碼: {bin_code}")
            return None
        
        # 先查本地快取
        if bin_code in self.cache:
            logger.info(f"從快取中找到 BIN {bin_code} 的銀行資訊")
            return self.cache[bin_code]
        
        logger.info(f"快取中沒有 BIN {bin_code} 的資訊，需要查詢外部 API")
        return None
    
    def add_bin_record(self, bin_code: str, bank_info: Dict[str, Any]) -> bool:
        """
        新增 BIN 記錄到快取
        
        Args:
            bin_code: 信用卡前6碼
            bank_info: 銀行資訊字典
            
        Returns:
            是否成功新增
        """
        if not bin_code or len(bin_code) != 6:
            logger.warning(f"無效的 BIN 碼: {bin_code}")
            return False
        
        try:
            # 新增記錄到快取
            self.cache[bin_code] = bank_info
            
            # 儲存到檔案
            success = self.save_cache()
            
            if success:
                logger.info(f"成功新增 BIN {bin_code} 記錄到快取")
            else:
                logger.error(f"新增 BIN {bin_code} 記錄失敗")
            
            return success
        except Exception as e:
            logger.error(f"新增 BIN {bin_code} 記錄時發生錯誤: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """清空快取"""
        try:
            self.cache = {}
            success = self.save_cache()
            
            if success:
                logger.info("成功清空 BIN 快取")
            else:
                logger.error("清空 BIN 快取失敗")
            
            return success
        except Exception as e:
            logger.error(f"清空 BIN 快取時發生錯誤: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """取得快取統計資訊"""
        return {
            'total_records': len(self.cache),
            'cache_file': self.cache_file,
            'file_exists': os.path.exists(self.cache_file),
            'file_size': os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0
        }


# 全域實例
bin_cache_service = BINCacheService()
