// Related HTML: templates/layouts/footer.html
export default () => ({
  email: '',
  isSubmitting: false,
  message: '',
  messageType: '',
  
  isValidEmail() {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(this.email);
  },
  
  async submitForm() {
    this.message = '';
    this.messageType = '';
    if (!this.email.trim()) { this.showMessage('請輸入 Email 地址。', 'error'); return; }
    if (!this.isValidEmail()) { this.showMessage('請輸入有效的 Email 地址。', 'error'); return; }
    this.isSubmitting = true;
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      this.showMessage('還在等訂閱?? 別等了，Rewardia沒有訂閱服務，聰明的你快去下載 Chrome extension 吧 !', 'success');
      this.email = '';
    } catch (error) {
      this.showMessage('訂閱失敗，請稍後再試。', 'error');
    } finally {
      this.isSubmitting = false;
    }
  },
  
  showMessage(text, type) {
    this.message = text;
    this.messageType = type;
    setTimeout(() => {
      this.message = '';
      this.messageType = '';
    }, 10000);
  }
});