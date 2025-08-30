import Alpine from "alpinejs";
import "htmx.org";
import message from './components/message.js';

import faq from './components/faq.js';
import login from './components/login.js';
import register from './components/register.js';
import subscribe from './components/subscribe.js';

window.Alpine = Alpine;

Alpine.data('faq_accordion', faq);
Alpine.data('login_form', login);
Alpine.data('register_form', register);
Alpine.data('subscribe_form', subscribe);
window.Alpine = Alpine;

Alpine.data('toast_fadeout', message);



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



//  register.html
Alpine.data('register_form', () => ({
  formData: {
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    agree_terms: false
  },

  errors: {},

  showPassword: false,
  showConfirmPassword: false,

  validateField(fieldName) {
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

    if (password.length < 8 || password.length > 20) {
      this.errors.password = '密碼長度必須在 8-20 個字元之間';
      return false;
    }

    if (!/^[a-zA-Z0-9]+$/.test(password)) {
      this.errors.password = '密碼只能包含英文字母和數字，不能有空格或特殊字元';
      return false;
    }

    if (!/[A-Z]/.test(password)) {
      this.errors.password = '密碼必須包含至少一個英文大寫字母';
      return false;
    }

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

}));




// login.html
Alpine.data('login_form', () => ({
  formData: {
    username: '',
    password: ''
  },

  errors: {},
  passwordVisible: false,

  togglePassword() {
    this.passwordVisible = !this.passwordVisible;
  },

  validateField(fieldName) {
    delete this.errors[fieldName];

    switch(fieldName) {
      case 'username':
        this.validateUsername();
        break;
      case 'password':
        this.validatePassword();
        break;
    }
  },

  validateUsername() {
    const username = this.formData.username.trim();

    if (!username) {
      this.errors.username = '帳號為必填項目';
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

    return true;
  },

  submitForm(event) {
    this.errors = {};

    const isUsernameValid = this.validateUsername();
    const isPasswordValid = this.validatePassword();

    if (isUsernameValid && isPasswordValid) {
      event.target.submit();
    }
  }
}));


// footer.html  訂閱~尚未處理完
Alpine.data('subscribe_form', () => ({
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

    if (!this.email.trim()) {
      this.showMessage('請輸入 Email 地址。', 'error');
      return;
    }

    if (!this.isValidEmail()) {
      this.showMessage('請輸入有效的 Email 地址。', 'error');
      return;
    }
    this.isSubmitting = true;

    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      this.showMessage('感謝您的訂閱！我們將儘快為您提供服務。', 'success');
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
}));

// 卡片表單的 Alpine.js 功能（清理版本）
Alpine.data('card_form', (config = {}) => ({
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
}));

Alpine.start();