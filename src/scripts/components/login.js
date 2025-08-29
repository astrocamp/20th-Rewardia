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