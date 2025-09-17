/**
 * Member Zone Component for Alpine.js
 * 處理會員專區的卡片刪除功能
 */

export default function memberZoneComponent() {
  return {
    // 卡片狀態
    showDeleteConfirm: false,
    isDeleting: false,
    
    // 初始化
    init() {
      // 可以在此處加入初始化邏輯
      console.log('Member zone component initialized');
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
        
        const response = await fetch(`/users/card/${cardId}/delete/`, {
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
            window.showToast('success', '刪除成功！');
          }
          // 重新載入頁面
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else {
          // 顯示錯誤訊息
          if (window.showToast) {
            window.showToast('error', data.message || '刪除失敗');
          }
          this.isDeleting = false;
        }
      } catch (error) {
        console.error('Delete card error:', error);
        if (window.showToast) {
          window.showToast('error', '刪除失敗，請稍後再試');
        }
        this.isDeleting = false;
      }
    },
    
    // 取得 CSRF token
    getCSRFToken() {
      const token = document.querySelector('[name=csrfmiddlewaretoken]');
      return token ? token.value : null;
    }
  };
}
