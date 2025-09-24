"""
BIN 服務整合模組
整合快取服務和外部 API 服務，提供完整的銀行辨識功能
"""
import logging
from typing import Optional, Dict, Any
from .bin_cache_service import get_bin_cache_service
from .bin_api_service import get_bin_api_service
from .bank_mapping import get_chinese_bank_name, is_bank_name_mapped

logger = logging.getLogger(__name__)


class BINService:
    """BIN 服務整合類別"""
    
    def __init__(self):
        self.cache_service = get_bin_cache_service()
        self.api_service = get_bin_api_service()
    
    def identify_bank_by_bin(self, bin_code: str) -> Dict[str, Any]:
        """
        根據 BIN 碼辨識銀行
        
        Args:
            bin_code: 信用卡前6碼
            
        Returns:
            辨識結果字典，包含：
            - success: 是否成功
            - bank_name_chinese: 中文銀行名稱
            - bank_name_english: 英文銀行名稱
            - card_type: 卡片類型
            - card_level: 卡片等級
            - country: 發卡國家
            - message: 訊息
            - from_cache: 是否來自快取
        """
        if not bin_code or len(bin_code) != 6:
            return {
                'success': False,
                'bank_name_chinese': '',
                'bank_name_english': '',
                'card_type': '',
                'card_level': '',
                'country': '',
                'message': '無效的 BIN 碼格式',
                'from_cache': False
            }
        
        # 步驟 1: 先查本地快取
        cached_result = self.cache_service.get_bank_by_bin(bin_code)
        
        if cached_result:
            logger.info(f"從快取中找到 BIN {bin_code} 的銀行資訊")
            return self._format_result(cached_result, from_cache=True)
        
        # 步驟 2: 查詢外部 API
        logger.info(f"快取中沒有 BIN {bin_code} 的資訊，查詢外部 API")
        api_result = self.api_service.query_bin_api(bin_code)
        
        if api_result:
            # 步驟 3: 儲存到快取
            success = self.cache_service.add_bin_record(bin_code, api_result)
            if success:
                logger.info(f"成功將 BIN {bin_code} 的資訊儲存到快取")
            else:
                logger.warning(f"儲存 BIN {bin_code} 的資訊到快取失敗")
            
            return self._format_result(api_result, from_cache=False)
        else:
            logger.warning(f"外部 API 無法辨識 BIN {bin_code}")
            return {
                'success': False,
                'bank_name_chinese': '',
                'bank_name_english': '',
                'card_type': '',
                'card_level': '',
                'country': '',
                'message': '銀行辨識失敗，請手動選擇發卡銀行名稱',
                'from_cache': False
            }
    
    def _format_result(self, api_data: Dict[str, Any], from_cache: bool) -> Dict[str, Any]:
        """
        格式化 API 回應資料
        
        Args:
            api_data: API 回應的原始資料
            from_cache: 是否來自快取
            
        Returns:
            格式化後的結果
        """
        try:
            # 取得英文銀行名稱
            bank_name_english = api_data.get('bank', '').strip()
            
            # 取得中文銀行名稱
            bank_name_chinese = get_chinese_bank_name(bank_name_english)
            
            # 檢查是否有對照的中文名稱
            has_mapping = is_bank_name_mapped(bank_name_english)
            
            # 如果沒有對照，記錄警告
            if not has_mapping:
                logger.warning(f"找不到銀行名稱對照: {bank_name_english}")
            
            # 構建結果
            result = {
                'success': True,
                'bank_name_chinese': bank_name_chinese,
                'bank_name_english': bank_name_english,
                'card_type': api_data.get('type', '').strip(),
                'card_level': api_data.get('level', '').strip(),
                'country': api_data.get('country', '').strip(),
                'country_code': api_data.get('countrycode', '').strip(),
                'website': api_data.get('website', '').strip(),
                'phone': api_data.get('phone', '').strip(),
                'valid': api_data.get('valid', 'false'),
                'from_cache': from_cache,
                'has_mapping': has_mapping
            }
            
            # 設定訊息
            if has_mapping:
                result['message'] = f'成功辨識銀行: {bank_name_chinese}'
            else:
                result['message'] = f'銀行辨識成功但無對照名稱: {bank_name_english}'
            
            return result
            
        except Exception as e:
            logger.error(f"格式化結果時發生錯誤: {e}")
            return {
                'success': False,
                'bank_name_chinese': '',
                'bank_name_english': '',
                'card_type': '',
                'card_level': '',
                'country': '',
                'message': '資料處理失敗',
                'from_cache': from_cache
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """取得快取統計資訊"""
        return self.cache_service.get_cache_stats()
    
    def clear_cache(self) -> bool:
        """清空快取"""
        return self.cache_service.clear_cache()
    
    def test_api_connection(self) -> bool:
        """測試 API 連線"""
        return self.api_service.test_api_connection()


# 全域實例（延遲初始化）
bin_service = None

def get_bin_service():
    """獲取 BIN 服務實例"""
    global bin_service
    if bin_service is None:
        bin_service = BINService()
    return bin_service
