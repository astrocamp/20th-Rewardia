export default (config = {}) => ({
  selectedBank: config.initialBankName || "",
  selectedCard: config.initialCardId || "",
  allCards: config.allCards || [],
  availableCards: [],
  
  // 新增：手動卡號輸入
  manualCardNumber: "",
  
  // 新增：相機擷取的卡號
  recognizedCardNumber: "",
  
  // 新增：卡片預覽資料
  cardPreview: {
    name: "",
    bank: "",
    imageUrl: ""
  },

  init() {
    this.updateAvailableCards(this.selectedBank);
    // 如果有初始選中的卡片，更新預覽
    if (this.selectedCard) {
      this.updateCardPreview();
    }
  },

  onBankChange() {
    this.updateAvailableCards(this.selectedBank);
    // 銀行變更時清空預覽
    this.clearCardPreview();
  },

  updateAvailableCards(bankName) {
    if (!bankName) {
      this.availableCards = [];
      this.selectedCard = "";
      return;
    }

    this.availableCards = this.allCards.filter(
      (card) => card.bankName === bankName
    );

    // 防呆：如果目前選中的卡不屬於新銀行 → 清空
    if (!this.availableCards.some((card) => card.id === this.selectedCard)) {
      this.selectedCard = "";
      this.clearCardPreview();
    }
  },

  // 新增：更新卡片預覽
  updateCardPreview() {
    if (!this.selectedCard) {
      this.clearCardPreview();
      return;
    }

    // 從 availableCards 中找到選中的卡片
    const selectedCardData = this.availableCards.find(
      (card) => card.id == this.selectedCard
    );

    if (selectedCardData) {
      // 使用卡片資料中的圖片 URL
      this.cardPreview = {
        name: selectedCardData.name,
        bank: selectedCardData.bankName,
        imageUrl: selectedCardData.imageUrl || ""
      };
    }
  },

  // 新增：清空卡片預覽
  clearCardPreview() {
    this.cardPreview = {
      name: "",
      bank: "",
      imageUrl: ""
    };
  },


  // 新增：處理手動卡號輸入
  formatCardInput(event) {
    // 只限制長度，不自動清理非數字字符
    let value = event.target.value;
    // 移除長度限制，讓使用者可以輸入完整的卡號
    this.manualCardNumber = value;
    event.target.value = value;
  },

  // 新增：表單提交前驗證
  validateForm() {
    // 檢查是否選擇了銀行和卡片
    if (!this.selectedBank || !this.selectedCard) {
      if (window.showToast) {
        window.showToast('請選擇銀行和卡片', 'error');
      }
      return false;
    }

    // 檢查卡號格式（如果提供了）- 卡號不是必填
    if (this.manualCardNumber && this.manualCardNumber.trim()) {
      // 先移除所有空白字符（包括空格、tab等），再檢查是否包含非數字字符
      const cleanNumber = this.manualCardNumber.replace(/\s+/g, '');
      if (/\D/.test(cleanNumber)) {
        if (window.showToast) {
          window.showToast('卡號只能包含數字，不允許字母或特殊符號', 'error');
        }
        return false;
      }
      
      // 檢查長度
      if (cleanNumber.length < 12 || cleanNumber.length > 19) {
        if (window.showToast) {
          window.showToast('卡號長度必須在12-19位之間', 'error');
        }
        return false;
      }
    }

    return true;
  },

  // 新增：表單提交處理
  submitForm(event) {
    // 執行前端驗證
    if (!this.validateForm()) {
      return false;
    }

    // 將手動輸入的卡號同步到隱藏欄位（移除空格）
    if (this.manualCardNumber) {
      this.recognizedCardNumber = this.manualCardNumber.replace(/\s/g, '');
    }
    
    // 使用 AJAX 提交表單，避免頁面重新載入
    const form = document.getElementById('card-form');
    if (form) {
      // 準備表單數據
      const formData = new FormData(form);
      formData.set('bank_name', this.selectedBank);
      formData.set('card_id', this.selectedCard);
      formData.set('card_number', this.recognizedCardNumber || '');
      
      // 發送 AJAX 請求
      fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        }
      })
      .then(response => response.text())
      .then(html => {
        // 更新頁面內容
        document.body.innerHTML = html;
        // 重新初始化 Alpine.js（避免重複初始化）
        if (window.Alpine && !window.Alpine._initialized) {
          window.Alpine.start();
        }
      })
      .catch(error => {
        console.error('Form submission error:', error);
        if (window.showToast) {
          window.showToast('提交失敗，請稍後再試', 'error');
        }
      });
    }
  }
});
