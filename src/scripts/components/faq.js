// Related HTML: templates/pages/faq.html
export default () => ({
  openItem: null,
  
  toggleItem(itemId) {
    if (this.openItem === itemId) {
      this.openItem = null;
    } else {
      this.openItem = itemId;
    }
  },
  
  isOpen(itemId) {
    return this.openItem === itemId;
  }
});