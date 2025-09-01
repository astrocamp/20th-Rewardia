export default (config = {}) => ({
  selectedBank: config.initialBankId || '',
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

  filterCardsByBank(bankId) {
    this.availableCards = this.allCards.filter(card => {
      return card.bankId.toString() === bankId.toString();
    });
  }
});