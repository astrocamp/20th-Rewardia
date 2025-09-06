export default (config = {}) => ({
  selectedBank: config.initialBankName || "",
  selectedCard: config.initialCardId || "",
  allCards: config.allCards || [],
  availableCards: [],

  init() {
    this.updateAvailableCards(this.selectedBank);
  },

  onBankChange() {
    this.updateAvailableCards(this.selectedBank);
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
    }
  },
});
