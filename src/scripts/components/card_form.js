export default (config = {}) => ({
  selectedBank: config.initialBankName || "",
  selectedCard: config.initialCardId || "",
  allCards: config.allCards || [],
  availableCards: [],
  
  // 新增：手動卡號輸入
  manualCardNumber: "",
  
  // 新增：相機擷取的卡號
  recognizedCardNumber: "",
  
  // 新增：BIN 辨識相關狀態
  bankRecognitionInProgress: false,
  bankRecognitionMessage: "",
  
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

    // 防呆：如果目前選中的卡不屬於新銀行 → 清空（但編輯模式保留初始值）
    if (!this.availableCards.some((card) => card.id == this.selectedCard)) {
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
    const input = event.target;
    const cursorPosition = input.selectionStart;
    const oldValue = input.value;
    
    // 移除非數字字符
    const cleaned = oldValue.replace(/\D/g, '');
    
    // 限制最多16位數字
    const limited = cleaned.substring(0, 16);
    
    // 每4位加空格
    const formatted = limited.replace(/(.{4})/g, '$1 ').trim();
    
    // 設置新值
    input.value = formatted;
    this.manualCardNumber = formatted;
    
    // 計算新的游標位置
    let newCursorPosition = cursorPosition;
    
    // 如果刪除了字符，游標位置需要調整
    if (formatted.length < oldValue.length) {
      const deletedChars = oldValue.length - formatted.length;
      newCursorPosition = Math.max(0, cursorPosition - deletedChars);
    } else if (formatted.length > oldValue.length) {
      const addedChars = formatted.length - oldValue.length;
      newCursorPosition = cursorPosition + addedChars;
    }
    
    // 設置游標位置
    this.$nextTick(() => {
      input.setSelectionRange(newCursorPosition, newCursorPosition);
    });
    
    // 檢查是否為16位數字，如果是則自動觸發銀行辨識
    console.log('卡號輸入檢測:', { formatted, cleanNumber: limited, length: limited.length }); // 調試用
    
    if (limited.length === 16) {
      console.log('觸發銀行辨識，BIN:', limited.substring(0, 6)); // 調試用
      this.identifyBankByBin(limited.substring(0, 6));
    } else {
      // 清除之前的辨識訊息
      this.bankRecognitionMessage = "";
    }
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
      if (cleanNumber.length !== 16) {
        if (window.showToast) {
          window.showToast('請輸入16位卡號', 'error');
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
      
      
      // 提交表單
      form.submit();
    }
  },

  // 新增：根據 BIN 碼辨識銀行
  async identifyBankByBin(binCode) {
    console.log('identifyBankByBin 被調用:', binCode); // 調試用
    
    if (!binCode || binCode.length !== 6) {
      console.log('BIN 碼無效:', binCode); // 調試用
      return;
    }

    this.bankRecognitionInProgress = true;
    this.bankRecognitionMessage = "";

    try {
      const response = await fetch('/users/api/identify-bank/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({
          bin_code: binCode
        })
      });

      const result = await response.json();

      if (result.success) {
        // 檢查是否有中文對照
        if (result.has_mapping) {
          // 有中文對照：自動填入銀行名稱
          // 自動填入銀行名稱
          this.selectedBank = result.bank_name_chinese;
          
          this.updateAvailableCards(this.selectedBank);
          this.bankRecognitionMessage = `✓ 銀行辨識成功：${result.bank_name_chinese}`;
          
          // 顯示友善提示
          if (window.showToast) {
            window.showToast(`銀行辨識成功：${result.bank_name_chinese}`, 'success');
          }
        } else {
          // 無中文對照：不清空選擇，只顯示提示讓用戶手動選擇
          this.bankRecognitionMessage = `銀行辨識成功：${result.bank_name_english}，但無中文對照，請手動選擇正確的銀行名稱`;
          
          // 顯示友善提示
          if (window.showToast) {
            window.showToast('銀行辨識成功但無中文對照，請手動選擇銀行名稱', 'warning');
          }
        }
      } else {
        // 辨識失敗，顯示友善提示
        this.bankRecognitionMessage = "銀行辨識失敗，請手動選擇銀行名稱";
        
        if (window.showToast) {
          window.showToast('銀行辨識失敗，請手動選擇銀行名稱', 'warning');
        }
      }
    } catch (error) {
      console.error('BIN 辨識錯誤:', error);
      this.bankRecognitionMessage = "銀行辨識服務暫時無法使用，請手動選擇銀行名稱";
      
      if (window.showToast) {
        window.showToast('銀行辨識服務暫時無法使用，請手動選擇銀行名稱', 'error');
      }
    } finally {
      this.bankRecognitionInProgress = false;
    }
  },

  // 新增：獲取 CSRF Token
  getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  }
});
