import Alpine from "alpinejs";
import "htmx.org";


window.Alpine = Alpine;

// FAQ 頁面的 Alpine.js 功能
Alpine.data('faq_accordion', () => ({
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
}));

// 註冊頁面的 Alpine.js 功能
Alpine.data('register_form', () => ({
  // 密碼顯示狀態追蹤
  passwordVisible: false,
  confirmPasswordVisible: false,
  
  // 切換密碼顯示/隱藏
  togglePassword(fieldType) {
    if (fieldType === 'password') {
      this.passwordVisible = !this.passwordVisible;
    } else if (fieldType === 'password_confirm') {
      this.confirmPasswordVisible = !this.confirmPasswordVisible;
    }
  },
  
}));

// 登入頁面的 Alpine.js 功能
Alpine.data('login_form', () => ({
  passwordVisible: false,
  
  togglePassword() {
    this.passwordVisible = !this.passwordVisible;
  },
}));

// 訂閱表單的 Alpine.js 功能
Alpine.data('subscribe_form', () => ({
  email: '',
  isSubmitting: false,
  message: '',
  messageType: '', // 'success' or 'error'
  
  // 驗證 email 格式
  isValidEmail() {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(this.email);
  },
  
  // 提交表單
  async submitForm() {
    // 重置訊息
    this.message = '';
    this.messageType = '';
    
    // 驗證 email
    if (!this.email.trim()) {
      this.showMessage('請輸入 Email 地址。', 'error');
      return;
    }
    
    if (!this.isValidEmail()) {
      this.showMessage('請輸入有效的 Email 地址。', 'error');
      return;
    }
    
    // 設定提交狀態
    this.isSubmitting = true;
    
    try {
      // 模擬提交過程（因為目前沒有後端實作）
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 成功訊息
      this.showMessage('感謝您的訂閱！我們將儘快為您提供服務。', 'success');
      this.email = ''; // 清空輸入
      
      // TODO: 實際的 API 呼叫應該在這裡
      // const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
      // const response = await fetch('/api/subscribe/', {
      //   method: 'POST',
      //   headers: { 
      //     'Content-Type': 'application/json',
      //     'X-CSRFToken': csrfToken
      //   },
      //   body: JSON.stringify({ email: this.email })
      // });
      
    } catch (error) {
      this.showMessage('訂閱失敗，請稍後再試。', 'error');
    } finally {
      this.isSubmitting = false;
    }
  },
  
  // 顯示訊息
  showMessage(text, type) {
    this.message = text;
    this.messageType = type;
    
    // 3秒後自動清除訊息
    setTimeout(() => {
      this.message = '';
      this.messageType = '';
    }, 3000);
  }
}));

Alpine.start();
