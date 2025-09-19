// 全域專業日誌記錄器
const isProduction = window.location.hostname !== 'localhost' && 
                     !window.location.hostname.includes('127.0.0.1') &&
                     !window.location.hostname.includes('dev');

const logger = {
  info: (message, data = {}) => {
    if (!isProduction) {
      console.log(`[Rewardia] ${message}`, data);
    }
  },
  warn: (message, data = {}) => {
    if (!isProduction) {
      console.warn(`[Rewardia] ${message}`, data);
    }
  },
  error: (message, data = {}) => {
    console.error(`[Rewardia] ${message}`, data); // 生產環境也保留錯誤記錄
  }
};

// 向後相容的 toastLogger
const toastLogger = {
  info: (message, data = {}) => logger.info(`Toast: ${message}`, data),
  warn: (message, data = {}) => logger.warn(`Toast: ${message}`, data),
  error: (message, data = {}) => logger.error(`Toast: ${message}`, data)
};

// 暴露全域 logger 供其他組件使用
window.RewardiaLogger = logger;

// 全域 toast 函數
window.showToast = function(message, type = 'info') {
  // 創建 toast 資料
  const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  const toastData = {
    id: toastId,
    message,
    type,
    visible: true
  };
  
  // 記錄 toast 顯示
  toastLogger.info(`顯示 ${type} toast`, { id: toastId, message });
  
  // 觸發自定義事件，讓頁面處理 toast 顯示
  window.dispatchEvent(new CustomEvent('show-toast', { 
    detail: toastData 
  }));
};

// toast_fadeout 組件
export default () => ({
  toasts: [], // 確保 toasts 始終是一個陣列
  
  init() {
    // 如果是 Django Messages，只對個別的 toast 元素執行淡出動畫，不移除容器
    const djangoToasts = this.$el.querySelectorAll('.tw-toast');
    if (djangoToasts.length > 0) {
      toastLogger.info(`初始化 ${djangoToasts.length} 個 Django Messages`);
      djangoToasts.forEach(toast => {
        setTimeout(() => {
          toast.style.opacity = '0';
          toast.style.transform = 'translateY(-6px)';
          setTimeout(() => toast.remove(), 200);
        }, 4000);
      });
    } else {
      toastLogger.info('Toast 容器已準備就緒，等待 JavaScript toasts');
    }
  },
  
  addToast(detail) {
    // 確保 toasts 是陣列
    if (!Array.isArray(this.toasts)) {
      toastLogger.error('toasts 不是陣列，重置為空陣列');
      this.toasts = [];
    }
    
    this.toasts.push(detail);
    toastLogger.info(`新增 toast`, { id: detail.id, type: detail.type, message: detail.message });
    
    // 3 秒後自動移除
    setTimeout(() => this.removeToast(detail.id), 3000);
  },
  
  removeToast(id) {
    // 確保 toasts 是陣列
    if (!Array.isArray(this.toasts)) {
      this.toasts = [];
      return;
    }
    
    const beforeCount = this.toasts.length;
    this.toasts = this.toasts.filter(t => t.id !== id);
    const afterCount = this.toasts.length;
    
    if (beforeCount > afterCount) {
      toastLogger.info(`移除 toast`, { id, remaining: afterCount });
    }
  }
});
