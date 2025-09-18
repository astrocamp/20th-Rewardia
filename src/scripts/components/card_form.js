export default (config = {}) => ({
  selectedBank: config.initialBankName || "",
  selectedCard: config.initialCardId || "",
  allCards: config.allCards || [],
  availableCards: [],
  
  // 新增：手動卡號輸入
  manualCardNumber: "",
  
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
    // 只允許數字，並限制長度
    let value = event.target.value.replace(/\D/g, '').slice(0, 19);
    this.manualCardNumber = value;
    event.target.value = value;
  }
});
