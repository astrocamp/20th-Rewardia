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
  // 表單資料
  formData: {
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    agree_terms: false
  },
  
  // 錯誤訊息
  errors: {},
  
  // 狀態管理
  isSubmitting: false,
  showPassword: false,
  showConfirmPassword: false,

  // 前端驗證函數
  validateField(fieldName) {
    // 清除該欄位的錯誤
    delete this.errors[fieldName];

    switch(fieldName) {
      case 'username':
        this.validateUsername();
        break;
      case 'email':
        this.validateEmail();
        break;
      case 'password':
        this.validatePassword();
        break;
      case 'confirm_password':
        this.validateConfirmPassword();
        break;
      case 'agree_terms':
        this.validateAgreeTerms();
        break;
    }
  },

  validateUsername() {
    const username = this.formData.username.trim();
    
    if (!username) {
      this.errors.username = '帳號為必填項目';
      return false;
    }
    
    // 檢查格式：只允許英文大小寫和數字，不能有空格
    if (!/^[a-zA-Z0-9]+$/.test(username)) {
      this.errors.username = '帳號只能包含英文字母和數字，不能有空格或特殊字元';
      return false;
    }
    
    return true;
  },

  validateEmail() {
    const email = this.formData.email.trim();
    
    if (!email) {
      this.errors.email = '電子信箱為必填項目';
      return false;
    }
    
    // 基本的 email 格式驗證
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      this.errors.email = '請輸入有效的電子信箱格式';
      return false;
    }
    
    return true;
  },

  validatePassword() {
    const password = this.formData.password;
    
    if (!password) {
      this.errors.password = '密碼為必填項目';
      return false;
    }
    
    // 檢查長度
    if (password.length < 8 || password.length > 20) {
      this.errors.password = '密碼長度必須在 8-20 個字元之間';
      return false;
    }
    
    // 檢查格式：只允許英文大小寫和數字，不能有空格
    if (!/^[a-zA-Z0-9]+$/.test(password)) {
      this.errors.password = '密碼只能包含英文字母和數字，不能有空格或特殊字元';
      return false;
    }
    
    // 檢查至少包含一個大寫字母
    if (!/[A-Z]/.test(password)) {
      this.errors.password = '密碼必須包含至少一個英文大寫字母';
      return false;
    }
    
    // 檢查至少包含一個小寫字母
    if (!/[a-z]/.test(password)) {
      this.errors.password = '密碼必須包含至少一個英文小寫字母';
      return false;
    }
    
    return true;
  },

  validateConfirmPassword() {
    const confirmPassword = this.formData.confirm_password;
    
    if (!confirmPassword) {
      this.errors.confirm_password = '確認密碼為必填項目';
      return false;
    }
    
    if (confirmPassword !== this.formData.password) {
      this.errors.confirm_password = '兩次輸入的密碼不一致，請重新確認';
      return false;
    }
    
    return true;
  },

  validateAgreeTerms() {
    if (!this.formData.agree_terms) {
      this.errors.agree_terms = '請勾選同意服務條款';
      return false;
    }
    
    return true;
  },

  // 驗證整個表單
  validateForm() {
    this.errors = {}; // 清除所有錯誤
    
    let isValid = true;
    
    // 檢查所有必填欄位是否有值
    if (!this.formData.username.trim()) {
      this.errors.username = '帳號為必填項目';
      isValid = false;
    }
    
    if (!this.formData.email.trim()) {
      this.errors.email = '電子信箱為必填項目';
      isValid = false;
    }
    
    if (!this.formData.password) {
      this.errors.password = '密碼為必填項目';
      isValid = false;
    }
    
    if (!this.formData.confirm_password) {
      this.errors.confirm_password = '確認密碼為必填項目';
      isValid = false;
    }
    
    if (!this.formData.agree_terms) {
      this.errors.agree_terms = '請勾選同意服務條款';
      isValid = false;
    }
    
    // 如果有缺少必填項目，直接返回，不進行格式驗證
    if (!isValid) {
      this.showAlert('請填寫所有必填項目', 'error');
      return false;
    }
    
    // 進行格式驗證
    isValid = this.validateUsername() && isValid;
    isValid = this.validateEmail() && isValid;
    isValid = this.validatePassword() && isValid;
    isValid = this.validateConfirmPassword() && isValid;
    
    return isValid;
  },

  // 提交表單
  async submitForm() {
    // 先進行前端驗證
    if (!this.validateForm()) {
      return;
    }
    
    this.isSubmitting = true;
    
    try {
      // 獲取 CSRF token
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
      
      const response = await fetch('/users/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(this.formData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        this.showAlert(result.message, 'success');
        
        // 等待 2 秒後跳轉到登入頁面
        setTimeout(() => {
          window.location.href = result.redirect_url;
        }, 2000);
      } else {
        // 處理後端驗證錯誤
        if (result.errors) {
          this.errors = result.errors;
        }
        
        if (result.message) {
          this.showAlert(result.message, 'error');
        }
      }
    } catch (error) {
      this.showAlert('系統錯誤，請稍後重試', 'error');
      console.error('Registration error:', error);
    } finally {
      this.isSubmitting = false;
    }
  },

  // 顯示提示訊息
  showAlert(message, type) {
    const alertContainer = type === 'error' ? 
      document.getElementById('error-alerts') : 
      document.getElementById('success-alerts');
    
    // 清除現有的提示
    document.getElementById('error-alerts').innerHTML = '';
    document.getElementById('success-alerts').innerHTML = '';
    
    const alertClass = type === 'error' ? 'alert alert-error' : 'alert alert-success';
    const alertHTML = `
      <div class="${alertClass}">
        <span>${message}</span>
      </div>
    `;
    
    alertContainer.innerHTML = alertHTML;
    
    // 自動隱藏提示（成功訊息除外）
    if (type === 'error') {
      setTimeout(() => {
        alertContainer.innerHTML = '';
      }, 5000);
    }
  }
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
