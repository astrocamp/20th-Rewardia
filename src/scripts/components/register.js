// Related HTML: templates/users/register.html
export default () => ({
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
      case 'username': this.validateUsername(); break;
      case 'email': this.validateEmail(); break;
      case 'password': this.validatePassword(); break;
      case 'confirm_password': this.validateConfirmPassword(); break;
      case 'agree_terms': this.validateAgreeTerms(); break;
    }
  },

  validateUsername() {
    const username = this.formData.username.trim();
    if (!username) { this.errors.username = '帳號為必填項目'; return false; }
    if (!/^[a-zA-Z0-9]+$/.test(username)) { this.errors.username = '帳號只能包含英文字母和數字，不能有空格或特殊字元'; return false; }
    return true;
  },

  validateEmail() {
    const email = this.formData.email.trim();
    if (!email) { this.errors.email = '電子信箱為必填項目'; return false; }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) { this.errors.email = '請輸入有效的電子信箱格式'; return false; }
    return true;
  },

  validatePassword() {
    const password = this.formData.password;
    if (!password) { this.errors.password = '密碼為必填項目'; return false; }
    if (password.length < 8 || password.length > 20) { this.errors.password = '密碼長度必須在 8-20 個字元之間'; return false; }
    if (!/^[a-zA-Z0-9]+$/.test(password)) { this.errors.password = '密碼只能包含英文字母和數字，不能有空格或特殊字元'; return false; }
    if (!/[A-Z]/.test(password)) { this.errors.password = '密碼必須包含至少一個英文大寫字母'; return false; }
    if (!/[a-z]/.test(password)) { this.errors.password = '密碼必須包含至少一個英文小寫字母'; return false; }
    return true;
  },

  validateConfirmPassword() {
    const confirmPassword = this.formData.confirm_password;
    if (!confirmPassword) { this.errors.confirm_password = '確認密碼為必填項目'; return false; }
    if (confirmPassword !== this.formData.password) { this.errors.confirm_password = '兩次輸入的密碼不一致，請重新確認'; return false; }
    return true;
  },

  validateAgreeTerms() {
    if (!this.formData.agree_terms) { this.errors.agree_terms = '請勾選同意服務條款'; return false; }
    return true;
  },

  submitForm(event) {
    this.errors = {};
    const isValid = this.validateUsername() && this.validateEmail() && this.validatePassword() && this.validateConfirmPassword() && this.validateAgreeTerms();
    if (isValid) {
      event.target.submit();
    }
  }
});