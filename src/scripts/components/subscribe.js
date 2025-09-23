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
      this.showMessage('感謝您的訂閱！我們將儘快為您提供服務。', 'success');
      console.log('還在等訂閱?? 趕快去下載 Chrome extension 吧 !');
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
    }, 3000);
  }
});