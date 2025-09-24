"""
BIN API 服務
用於查詢外部 BIN 檢查 API 來取得信用卡發卡銀行資訊
"""
import requests
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class BINAPIService:
    """BIN API 服務類別"""
    
    def __init__(self):
        # BIN API 配置
        self.api_base_url = "https://api.bincodes.com/bin/"
        self.api_key = getattr(settings, 'BIN_API_KEY', None)
        self.timeout = 10  # 請求超時時間（秒）
    
    def query_bin_api(self, bin_code: str) -> Optional[Dict[str, Any]]:
        """
        查詢外部 BIN API
        
        Args:
            bin_code: 信用卡前6碼
            
        Returns:
            銀行資訊字典，包含 bank, card, type 等資訊，如果查詢失敗則返回 None
        """
        if not bin_code or len(bin_code) != 6:
            logger.warning(f"無效的 BIN 碼: {bin_code}")
            return None
        
        if not self.api_key:
            logger.error("BIN API Key 未設定")
            return None
        
        try:
            # 構建 API 請求 URL
            url = f"{self.api_base_url}?format=json&api_key={self.api_key}&bin={bin_code}"
            
            logger.info(f"查詢 BIN API: {bin_code}")
            
            # 發送請求
            response = requests.get(url, timeout=self.timeout)
            
            # 檢查回應狀態
            if response.status_code == 200:
                data = response.json()
                
                # 檢查 API 回應是否有效
                if self._is_valid_response(data):
                    logger.info(f"成功查詢 BIN {bin_code}: {data.get('bank', 'Unknown')}")
                    return data
                else:
                    logger.warning(f"BIN API 返回無效資料: {data}")
                    return None
            else:
                logger.error(f"BIN API 請求失敗: HTTP {response.status_code}")
                logger.error(f"錯誤回應: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"BIN API 請求超時: {bin_code}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"BIN API 請求錯誤: {e}")
            return None
        except Exception as e:
            logger.error(f"查詢 BIN API 時發生未預期錯誤: {e}")
            return None
    
    def _is_valid_response(self, data: Dict[str, Any]) -> bool:
        """
        檢查 API 回應是否有效
        
        Args:
            data: API 回應資料
            
        Returns:
            是否為有效回應
        """
        if not isinstance(data, dict):
            return False
        
        # 檢查必要欄位
        required_fields = ['bin', 'bank']
        for field in required_fields:
            if field not in data:
                logger.warning(f"API 回應缺少必要欄位: {field}")
                return False
        
        # 檢查銀行名稱是否為空
        bank_name = data.get('bank', '').strip()
        if not bank_name:
            logger.warning("API 回應的銀行名稱為空")
            return False
        
        # 檢查 BIN 碼是否匹配
        returned_bin = data.get('bin', '').strip()
        if not returned_bin:
            logger.warning("API 回應的 BIN 碼為空")
            return False
        
        return True
    
    def test_api_connection(self) -> bool:
        """
        測試 API 連線
        
        Returns:
            連線是否正常
        """
        if not self.api_key:
            logger.error("BIN API Key 未設定，無法測試連線")
            return False
        
        try:
            # 使用一個測試用的 BIN 碼
            test_bin = "515735"  # 這是 API 文檔中的範例 BIN
            result = self.query_bin_api(test_bin)
            
            if result:
                logger.info("BIN API 連線測試成功")
                return True
            else:
                logger.error("BIN API 連線測試失敗")
                return False
                
        except Exception as e:
            logger.error(f"BIN API 連線測試時發生錯誤: {e}")
            return False


# 全域實例
bin_api_service = BINAPIService()
