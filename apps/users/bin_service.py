"""
BIN 服務整合模組
使用外部 API 服務進行銀行辨識(目前上限一天20次查詢free)
"""
import logging
from typing import Optional, Dict, Any
from .bin_api_service import get_bin_api_service
from .bank_mapping import get_chinese_bank_name, is_bank_name_mapped

logger = logging.getLogger(__name__)


class BINService:
    """BIN 服務整合類別"""
    
    def __init__(self):
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
        """
        if not bin_code or len(bin_code) != 6:
            return {
                'success': False,
                'bank_name_chinese': '',
                'bank_name_english': '',
                'card_type': '',
                'card_level': '',
                'country': '',
                'message': '無效的 BIN 碼格式'
            }
        
        # 直接查詢外部 API
        logger.info(f"查詢外部 API 辨識 BIN {bin_code}")
        api_result = self.api_service.query_bin_api(bin_code)
        
        if api_result:
            logger.info(f"成功從外部 API 辨識 BIN {bin_code}")
            return self._format_result(api_result)
        else:
            logger.warning(f"外部 API 無法辨識 BIN {bin_code}")
            return {
                'success': False,
                'bank_name_chinese': '',
                'bank_name_english': '',
                'card_type': '',
                'card_level': '',
                'country': '',
                'message': '銀行辨識服務暫時無法使用，請手動選擇發卡銀行名稱'
            }
    
    def _format_result(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化 API 回應資料
        
        Args:
            api_data: API 回應的原始資料
            
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
                'message': '資料處理失敗'
            }
    
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
