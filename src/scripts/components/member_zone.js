/**
 * Member Zone Component for Alpine.js
 * 處理會員專區的卡片刪除功能
 */

export default function memberZoneComponent() {
  return {
    // 卡片狀態
    showDeleteConfirm: false,
    isDeleting: false,
    
    // 新增卡號狀態
    showAddCardDialog: false,
    showManualInput: false,
    manualCardNumber: '',
    
    
    // 初始化
    init() {
      // 可以在此處加入初始化邏輯
    },
    
    // 顯示刪除確認對話框
    showDeleteDialog() {
      this.showDeleteConfirm = true;
    },
    
    // 隱藏刪除確認對話框
    hideDeleteDialog() {
      this.showDeleteConfirm = false;
      this.isDeleting = false;
    },
    
    // 顯示新增卡號對話框
    showAddCardNumberDialog() {
      this.showAddCardDialog = true;
    },
    
    // 隱藏新增卡號對話框
    hideAddCardNumberDialog() {
      this.showAddCardDialog = false;
    },
    
    // 顯示手動輸入對話框
    showManualInputDialog() {
      this.showAddCardDialog = false;
      this.showManualInput = true;
      this.manualCardNumber = '';
    },
    
    // 隱藏手動輸入對話框
    hideManualInputDialog() {
      this.showManualInput = false;
      this.manualCardNumber = '';
    },
    
    // 格式化卡號輸入
    formatCardInput(event) {
      let value = event.target.value.replace(/\D/g, ''); // 只保留數字
      
      // 每4位數字加一個空格
      value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
      
      this.manualCardNumber = value;
      event.target.value = value;
    },
    
    // 確認手動輸入
    async confirmManualInput(cardId) {
      const cleanNumber = this.manualCardNumber.replace(/\s/g, '');
      if (!this.manualCardNumber || cleanNumber.length < 12 || cleanNumber.length > 19) {
        if (window.showToast) {
          window.showToast('請輸入12-19位卡號', 'error');
        }
        return;
      }
      
      try {
        const cardNumber = this.manualCardNumber.replace(/\s/g, ''); // 移除空格
        
        const response = await fetch(`/users/card/${cardId}/add-number/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': this.getCSRFToken(),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            card_number: cardNumber
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          if (window.showToast) {
            window.showToast('卡號新增成功！', 'success');
          }
          this.hideManualInputDialog();
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else {
          if (window.showToast) {
            window.showToast(data.message || '新增失敗', 'error');
          }
        }
      } catch (error) {
        console.error('Add card number error:', error);
        if (window.showToast) {
          window.showToast('新增失敗，請稍後再試', 'error');
        }
      }
    },
    
    // 開始相機擷取
    startCameraCapture(cardId) {
      console.log('startCameraCapture called with cardId:', cardId);
      this.hideAddCardNumberDialog();
      // 觸發全域事件開啟相機，並傳遞卡片 ID
      this.$dispatch('open-camera', { cardId: cardId });
      console.log('Dispatched open-camera event with cardId:', cardId);
    },
    
    // 刪除卡片
    async deleteCard(cardId) {
      if (this.isDeleting) return;
      
      this.isDeleting = true;
      
      try {
        // 取得 CSRF token
        const csrfToken = this.getCSRFToken();
        if (!csrfToken) {
          throw new Error('無法找到 CSRF token');
        }
        
        const response = await fetch(`/users/cards/${cardId}/delete/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
          // 顯示成功訊息
          if (window.showToast) {
            window.showToast('刪除成功！', 'success');
          }
          // 重新載入頁面
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else {
          // 顯示錯誤訊息
          if (window.showToast) {
            window.showToast(data.message || '刪除失敗', 'error');
          }
          this.isDeleting = false;
        }
      } catch (error) {
        console.error('Delete card error:', error);
        if (window.showToast) {
          window.showToast('刪除失敗，請稍後再試', 'error');
        }
        this.isDeleting = false;
      }
    },
    
    // 取得 CSRF token
    getCSRFToken() {
      const token = document.querySelector('[name=csrfmiddlewaretoken]');
      return token ? token.value : null;
    },
    
  };
}
