// Related HTML: templates/admins/image_upload.html
export default () => ({
  cards: [], // 信用卡資料陣列
  selectedFiles: {}, // 儲存選擇的檔案 {cardId: {file, preview, name}}
  selectedCards: [], // 選中的卡片 ID 陣列
  isLoading: false,
  loadingMessage: '處理中...',
  
  // 初始化
  async init() {
    await this.loadCards();
  },
  
  // 載入信用卡資料
  async loadCards() {
    try {
      const data = await this.apiRequest('/admins/api/cards/');
      this.cards = data.cards;
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('載入信用卡資料失敗:', error);
      }
      this.showError('載入信用卡資料失敗');
    }
  },
  
  // 處理檔案選擇
  handleFileSelect(event, cardId) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 驗證檔案類型
    if (!file.type.startsWith('image/')) {
      this.showError('請選擇圖片檔案');
      return;
    }
    
    // 驗證檔案大小 (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      this.showError('檔案大小不能超過 10MB');
      return;
    }
    
    // 釋放舊的 blob URL (防止記憶體洩漏)
    if (this.selectedFiles[cardId]?.preview) {
      URL.revokeObjectURL(this.selectedFiles[cardId].preview);
    }
    
    // 創建預覽 URL
    const preview = URL.createObjectURL(file);
    
    // 使用 Alpine.js 響應性更新方式
    this.selectedFiles = {
      ...this.selectedFiles,
      [cardId]: {
        file: file,
        preview: preview,
        name: file.name,
        size: this.formatFileSize(file.size)
      }
    };
    
  },
  
  // 格式化檔案大小
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },
  
  // 上傳單張圖片
  async uploadImage(cardId) {
    if (!this.selectedFiles[cardId]) {
      this.showError('請先選擇圖片');
      return;
    }
    
    this.isLoading = true;
    this.loadingMessage = '上傳圖片中...';
    
    try {
      await this.uploadSingleCard(cardId);
      this.showSuccess('圖片上傳成功');
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('上傳圖片失敗:', error);
      }
      this.showError('上傳圖片失敗: ' + error.message);
    } finally {
      this.isLoading = false;
    }
  },

  // 刪除單張圖片
  async deleteImage(cardId) {
    if (!confirm('確定要刪除這張圖片嗎？')) {
      return;
    }
    
    this.isLoading = true;
    this.loadingMessage = '刪除圖片中...';
    
    try {
      await this.deleteSingleCard(cardId);
      this.showSuccess('圖片刪除成功');
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error('刪除圖片失敗:', error);
      }
      this.showError('刪除圖片失敗: ' + error.message);
    } finally {
      this.isLoading = false;
    }
  },
  
  // 批次操作通用方法
  async batchOperation(operation, actionName) {
    const selectedCardIds = this.getValidSelectedCards(operation);
    
    if (selectedCardIds.length === 0) {
      this.showError(`請選擇要${actionName}的圖片`);
      return;
    }
    
    if (operation === 'delete' && !confirm(`確定要刪除 ${selectedCardIds.length} 張圖片嗎？`)) {
      return;
    }
    
    this.isLoading = true;
    this.loadingMessage = `批次${actionName} ${selectedCardIds.length} 張圖片中...`;
    
    try {
      const results = await this.processCardsBatch(selectedCardIds, operation);
      this.handleBatchResults(results, actionName);
    } catch (error) {
      if (window.RewardiaLogger) {
        window.RewardiaLogger.error(`批次${actionName}過程中發生錯誤:`, error);
      }
      this.showError(`批次${actionName}過程中發生錯誤`);
      this.isLoading = false;
      this.selectedCards = [];
    }
  },

  // 獲取有效的選中卡片
  getValidSelectedCards(operation) {
    return this.selectedCards.filter(cardId => {
      const card = this.cards.find(c => c.id === cardId);
      if (operation === 'upload') {
        return card && this.selectedFiles[cardId]?.file;
      } else if (operation === 'delete') {
        return card && card.image;
      }
      return false;
    });
  },

  // 批次處理卡片
  async processCardsBatch(cardIds, operation) {
    const results = { success: 0, error: 0 };
    const total = cardIds.length;
    
    for (let i = 0; i < cardIds.length; i++) {
      const cardId = cardIds[i];
      const current = i + 1;
      
      // 更新進度訊息
      this.loadingMessage = `批次${operation === 'upload' ? '上傳' : '刪除'} ${current}/${total} 張圖片中...`;
      
      try {
        if (operation === 'upload') {
          await this.uploadSingleCard(cardId);
        } else if (operation === 'delete') {
          await this.deleteSingleCard(cardId);
        }
        results.success++;
      } catch (error) {
        results.error++;
        if (window.RewardiaLogger) {
          window.RewardiaLogger.error(`卡片 ${cardId} ${operation === 'upload' ? '上傳' : '刪除'}失敗:`, error);
        }
      }
    }
    
    return results;
  },

  // 處理批次結果
  handleBatchResults(results, actionName) {
    this.isLoading = false;
    
    if (results.success > 0) {
      const message = `批次${actionName}完成: 成功 ${results.success} 張${results.error > 0 ? `，失敗 ${results.error} 張` : ''}`;
      this.showSuccess(message);
    } else {
      this.showError(`批次${actionName}失敗`);
    }
    
    this.selectedCards = [];
  },

  // 批次上傳
  async batchUpload() {
    await this.batchOperation('upload', '上傳');
  },

  // 批次刪除
  async batchDelete() {
    await this.batchOperation('delete', '刪除');
  },

  // 單張上傳（內部方法）
  async uploadSingleCard(cardId) {
    const selectedFile = this.selectedFiles[cardId];
    const formData = new FormData();
    formData.append('image', selectedFile.file);
    formData.append('card_id', cardId);
    formData.append('csrfmiddlewaretoken', this.getCSRFToken());
    
    const result = await this.apiRequest('/admins/api/upload-image/', {
      method: 'POST',
      body: formData
    });
    
    if (result.success) {
      this.updateCardData(cardId, result.image_url, result.last_modified);
      
      // 釋放 blob URL 並清除選擇的檔案
      if (this.selectedFiles[cardId]?.preview) {
        URL.revokeObjectURL(this.selectedFiles[cardId].preview);
      }
      delete this.selectedFiles[cardId];
    } else {
      throw new Error(result.error || '上傳失敗');
    }
  },

  // 單張刪除（內部方法）
  async deleteSingleCard(cardId) {
    const formData = new FormData();
    formData.append('card_id', cardId);
    formData.append('csrfmiddlewaretoken', this.getCSRFToken());
    
    const result = await this.apiRequest('/admins/api/delete-image/', {
      method: 'POST',
      body: formData
    });
    
    if (result.success) {
      this.updateCardData(cardId, null, result.last_modified);
    } else {
      throw new Error(result.error || '刪除失敗');
    }
  },

  // 更新卡片資料（統一方法）
  updateCardData(cardId, imageUrl, lastModified) {
    const card = this.cards.find(c => c.id === cardId);
    if (card) {
      card.image = imageUrl;
      card.last_modified = lastModified || '剛剛';
    }
  },
  
  // 切換單個卡片選擇
  toggleSelectCard(cardId) {
    const index = this.selectedCards.indexOf(cardId);
    if (index > -1) {
      this.selectedCards.splice(index, 1);
    } else {
      this.selectedCards.push(cardId);
    }
  },
  
  // 全選/取消全選
  toggleSelectAll(event) {
    if (event.target.checked) {
      this.selectedCards = this.cards.map(card => card.id);
    } else {
      this.selectedCards = [];
    }
  },
  
  // 檢查是否有選中的項目
  hasSelectedItems() {
    return this.selectedCards.length > 0;
  },
  
  // 檢查是否全選
  isAllSelected() {
    return this.selectedCards.length === this.cards.length && this.cards.length > 0;
  },
  
  // 統一的 API 請求方法
  async apiRequest(url, options = {}) {
    const defaultOptions = {
      headers: {
        'X-CSRFToken': this.getCSRFToken(),
        ...options.headers
      }
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    if (!response.ok) {
      let errorMessage = '請求失敗';
      switch (response.status) {
        case 400:
          errorMessage = '請求參數錯誤';
          break;
        case 403:
          errorMessage = '權限不足或 CSRF token 錯誤';
          break;
        case 404:
          errorMessage = '找不到指定的資源';
          break;
        case 413:
          errorMessage = '檔案太大';
          break;
        case 500:
          errorMessage = '伺服器內部錯誤';
          break;
        default:
          errorMessage = `請求失敗 (${response.status})`;
      }
      throw new Error(errorMessage);
    }
    
    return await response.json();
  },

  // 獲取 CSRF Token
  getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
  },
  
  // 顯示成功訊息
  showSuccess(message) {
    if (window.RewardiaLogger) {
      window.RewardiaLogger.info('成功:', message);
    }
    if (window.showToast) {
      window.showToast(message, 'success');
    }
  },
  
  // 顯示錯誤訊息
  showError(message) {
    if (window.RewardiaLogger) {
      window.RewardiaLogger.error('錯誤:', message);
    }
    if (window.showToast) {
      window.showToast(message, 'error');
    }
  }
});
