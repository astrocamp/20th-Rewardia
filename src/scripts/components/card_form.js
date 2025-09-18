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
        window.showToast('請選擇銀行與卡片', 'error');
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
    if (this.manualCardNumber && this.manualCardNumber.trim()) {
      this.recognizedCardNumber = this.manualCardNumber.replace(/\s/g, '');
    } else {
      this.recognizedCardNumber = '';
    }
    
    // 使用傳統表單提交，確保轉址和訊息都能正常工作
    const form = document.getElementById('card-form');
    if (form) {
      // 設置表單數據
      const bankNameInput = form.querySelector('[name="bank_name"]');
      const cardIdInput = form.querySelector('[name="card_id"]');
      const cardNumberInput = form.querySelector('[name="card_number"]');
      
      if (bankNameInput) bankNameInput.value = this.selectedBank;
      if (cardIdInput) cardIdInput.value = this.selectedCard;
      if (cardNumberInput) cardNumberInput.value = this.recognizedCardNumber || '';
      
      // 調試信息
      console.log('Form submission debug:', {
        bank_name: this.selectedBank,
        card_id: this.selectedCard,
        card_number: this.recognizedCardNumber,
        manualCardNumber: this.manualCardNumber
      });
      
      // 提交表單
      form.submit();
    }
  }
});
