export default (config = {}) => ({
  selectedBank: config.initialBankName || '',
  selectedCard: config.initialCardId || '',
  allCards: config.allCards || [],
  availableCards: [],

  init() {
    if (this.selectedBank) {
      this.filterCardsByBank(this.selectedBank);
    }
  },

  onBankChange() {
    if (this.selectedBank) {
      this.selectedCard = '';
      this.filterCardsByBank(this.selectedBank);
    } else {
      this.availableCards = [];
      this.selectedCard = '';
    }
  },

  filterCardsByBank(bankName) {
    this.availableCards = this.allCards.filter(card => {
      return card.bankName === bankName;
    });
  }
});