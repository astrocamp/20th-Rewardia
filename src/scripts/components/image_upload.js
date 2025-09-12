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
      const response = await fetch('/admins/api/cards/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      this.cards = data.cards.map(card => ({
        ...card,
        // 直接使用後端回傳的 last_modified，不需要重新映射
      }));
    } catch (error) {
      console.error('載入信用卡資料失敗:', error);
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
    
    // 創建預覽 URL
    const preview = URL.createObjectURL(file);
    
    // 儲存檔案資訊
    this.selectedFiles[cardId] = {
      file: file,
      preview: preview,
      name: file.name,
      size: this.formatFileSize(file.size)
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
    const selectedFile = this.selectedFiles[cardId];
    if (!selectedFile) {
      this.showError('請先選擇圖片');
      return;
    }
    
    this.isLoading = true;
    this.loadingMessage = '上傳圖片中...';
    
    try {
      const formData = new FormData();
      formData.append('image', selectedFile.file);
      formData.append('card_id', cardId);
      
      const response = await fetch('/admins/api/upload-image/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': this.getCSRFToken()
        }
      });
      
      if (!response.ok) {
        throw new Error(`上傳失敗: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // 更新卡片資料
        const card = this.cards.find(c => c.id === cardId);
        if (card) {
          card.image = result.image_url;
          card.last_modified = result.last_modified || new Date().toLocaleString();
        }
        
        // 清除選擇的檔案
        delete this.selectedFiles[cardId];
        
        this.showSuccess('圖片上傳成功');
      } else {
        throw new Error(result.error || '上傳失敗');
      }
    } catch (error) {
      console.error('上傳圖片失敗:', error);
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
      const response = await fetch('/admins/api/delete-image/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({ card_id: cardId })
      });
      
      if (!response.ok) {
        throw new Error(`刪除失敗: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // 更新卡片資料
        const card = this.cards.find(c => c.id === cardId);
        if (card) {
          card.image = null;
          card.last_modified = result.last_modified || new Date().toLocaleString();
        }
        
        this.showSuccess('圖片刪除成功');
      } else {
        throw new Error(result.error || '刪除失敗');
      }
    } catch (error) {
      console.error('刪除圖片失敗:', error);
      this.showError('刪除圖片失敗: ' + error.message);
    } finally {
      this.isLoading = false;
    }
  },
  
  // 批次上傳
  async batchUpload() {
    const selectedCardIds = this.selectedCards.filter(cardId => 
      this.selectedFiles[cardId] && this.selectedFiles[cardId].file
    );
    
    if (selectedCardIds.length === 0) {
      this.showError('請選擇要上傳的圖片');
      return;
    }
    
    this.isLoading = true;
    this.loadingMessage = `批次上傳 ${selectedCardIds.length} 張圖片中...`;
    
    let successCount = 0;
    let errorCount = 0;
    
    for (const cardId of selectedCardIds) {
      try {
        const selectedFile = this.selectedFiles[cardId];
        const formData = new FormData();
        formData.append('image', selectedFile.file);
        formData.append('card_id', cardId);
        
        const response = await fetch('/admins/api/upload-image/', {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': this.getCSRFToken()
          }
        });
        
        if (!response.ok) {
          throw new Error(`上傳失敗: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
          // 更新卡片資料
          const card = this.cards.find(c => c.id === cardId);
          if (card) {
            card.image = result.image_url;
            card.last_modified = result.last_modified || new Date().toLocaleString();
          }
          
          // 清除選擇的檔案
          delete this.selectedFiles[cardId];
          
          successCount++;
        } else {
          throw new Error(result.error || '上傳失敗');
        }
      } catch (error) {
        errorCount++;
        console.error(`卡片 ${cardId} 上傳失敗:`, error);
      }
    }
    
    this.isLoading = false;
    
    if (successCount > 0) {
      this.showSuccess(`批次上傳完成: 成功 ${successCount} 張${errorCount > 0 ? `，失敗 ${errorCount} 張` : ''}`);
    } else {
      this.showError('批次上傳失敗');
    }
    
    // 清除選擇
    this.selectedCards = [];
  },
  
  // 批次刪除
  async batchDelete() {
    const selectedCardIds = this.selectedCards.filter(cardId => {
      const card = this.cards.find(c => c.id === cardId);
      return card && card.image;
    });
    
    if (selectedCardIds.length === 0) {
      this.showError('請選擇要刪除的圖片');
      return;
    }
    
    if (!confirm(`確定要刪除 ${selectedCardIds.length} 張圖片嗎？`)) {
      return;
    }
    
    this.isLoading = true;
    this.loadingMessage = `批次刪除 ${selectedCardIds.length} 張圖片中...`;
    
    let successCount = 0;
    let errorCount = 0;
    
    for (const cardId of selectedCardIds) {
      try {
        const response = await fetch('/admins/api/delete-image/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
          },
          body: JSON.stringify({ card_id: cardId })
        });
        
        if (!response.ok) {
          throw new Error(`刪除失敗: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
          // 更新卡片資料
          const card = this.cards.find(c => c.id === cardId);
          if (card) {
            card.image = null;
            card.last_modified = result.last_modified || new Date().toLocaleString();
          }
          
          successCount++;
        } else {
          throw new Error(result.error || '刪除失敗');
        }
      } catch (error) {
        errorCount++;
        console.error(`卡片 ${cardId} 刪除失敗:`, error);
      }
    }
    
    this.isLoading = false;
    
    if (successCount > 0) {
      this.showSuccess(`批次刪除完成: 成功 ${successCount} 張${errorCount > 0 ? `，失敗 ${errorCount} 張` : ''}`);
    } else {
      this.showError('批次刪除失敗');
    }
    
    // 清除選擇
    this.selectedCards = [];
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
  
  // 獲取 CSRF Token
  getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
  },
  
  // 顯示成功訊息
  showSuccess(message) {
    // 可以在這裡添加 toast 通知
    console.log('Success:', message);
    alert(message); // 臨時使用 alert，可以替換為更好的通知系統
  },
  
  // 顯示錯誤訊息
  showError(message) {
    // 可以在這裡添加 toast 通知
    console.error('Error:', message);
    alert(message); // 臨時使用 alert，可以替換為更好的通知系統
  }
});
