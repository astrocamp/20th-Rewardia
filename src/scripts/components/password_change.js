// Related HTML: templates/users/member_zone.html (password change modal)
export default () => ({
  // 修改密碼相關屬性
  showPasswordModal: false,
  passwordChangeData: {
    old_password: '',
    new_password: '',
    confirm_new_password: ''
  },
  passwordChangeErrors: {},
  showOldPassword: false,
  showNewPassword: false,
  showConfirmNewPassword: false,
  isSubmittingPassword: false,

  // 開啟修改密碼彈窗
  openPasswordModal() {
    this.showPasswordModal = true;
    this.resetPasswordForm();
  },

  // 關閉修改密碼彈窗
  closePasswordModal() {
    this.showPasswordModal = false;
    this.resetPasswordForm();
  },

  // 重置修改密碼表單
  resetPasswordForm() {
    this.passwordChangeData = {
      old_password: '',
      new_password: '',
      confirm_new_password: ''
    };
    this.passwordChangeErrors = {};
    this.showOldPassword = false;
    this.showNewPassword = false;
    this.showConfirmNewPassword = false;
    this.isSubmittingPassword = false;
  },

  // 驗證修改密碼欄位
  validatePasswordField(fieldName) {
    delete this.passwordChangeErrors[fieldName];
    switch(fieldName) {
      case 'old_password': this.validateOldPassword(); break;
      case 'new_password': this.validateNewPassword(); break;
      case 'confirm_new_password': this.validateConfirmNewPassword(); break;
    }
  },

  // 清除修改密碼欄位錯誤
  clearPasswordFieldError(fieldName) {
    delete this.passwordChangeErrors[fieldName];
  },

  // 驗證舊密碼
  validateOldPassword() {
    const oldPassword = this.passwordChangeData.old_password.trim();
    if (!oldPassword) { 
      this.passwordChangeErrors.old_password = '舊密碼為必填項目'; 
      return false; 
    }
    return true;
  },

  // 驗證新密碼（複製自 register.js 的 validatePassword 函數）
  validateNewPassword() {
    const password = this.passwordChangeData.new_password;
    if (!password) { 
      this.passwordChangeErrors.new_password = '新密碼為必填項目'; 
      return false; 
    }
    if (password.length < 8 || password.length > 20) { 
      this.passwordChangeErrors.new_password = '密碼長度必須在 8-20 個字元之間'; 
      return false; 
    }
    if (!/^[a-zA-Z0-9]+$/.test(password)) { 
      this.passwordChangeErrors.new_password = '密碼只能包含英文字母和數字，不能有空格或特殊字元'; 
      return false; 
    }
    if (!/[A-Z]/.test(password)) { 
      this.passwordChangeErrors.new_password = '密碼必須包含至少一個英文大寫字母'; 
      return false; 
    }
    if (!/[a-z]/.test(password)) { 
      this.passwordChangeErrors.new_password = '密碼必須包含至少一個英文小寫字母'; 
      return false; 
    }
    if (!/[0-9]/.test(password)) { 
      this.passwordChangeErrors.new_password = '密碼必須包含至少一個數字'; 
      return false; 
    }
    // 檢查新密碼是否與舊密碼相同
    if (password === this.passwordChangeData.old_password) {
      this.passwordChangeErrors.new_password = '新密碼不能與舊密碼相同';
      return false;
    }
    return true;
  },

  // 驗證確認新密碼（複製自 register.js 的 validateConfirmPassword 函數）
  validateConfirmNewPassword() {
    const confirmPassword = this.passwordChangeData.confirm_new_password;
    if (!confirmPassword) { 
      this.passwordChangeErrors.confirm_new_password = '確認密碼為必填項目'; 
      return false; 
    }
    if (confirmPassword !== this.passwordChangeData.new_password) { 
      this.passwordChangeErrors.confirm_new_password = '兩次輸入的密碼不一致，請重新確認'; 
      return false; 
    }
    return true;
  },

  // 檢查修改密碼表單是否有效
  isPasswordFormValid() {
    return this.passwordChangeData.old_password.trim() && 
           this.passwordChangeData.new_password.trim() && 
           this.passwordChangeData.confirm_new_password.trim() &&
           !this.passwordChangeErrors.old_password &&
           !this.passwordChangeErrors.new_password &&
           !this.passwordChangeErrors.confirm_new_password;
  },

  // 提交修改密碼表單
  async submitPasswordChange() {
    // 注意：成功後會重定向到會員專區，Django Messages 會顯示成功訊息
    // 先進行前端驗證
    this.passwordChangeErrors = {};
    const isValid = this.validateOldPassword() && this.validateNewPassword() && this.validateConfirmNewPassword();
    
    if (!isValid) {
      return;
    }

    this.isSubmittingPassword = true;

    try {
      const response = await fetch('/users/change-password/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
          old_password: this.passwordChangeData.old_password,
          new_password: this.passwordChangeData.new_password,
          confirm_password: this.passwordChangeData.confirm_new_password
        })
      });

      const data = await response.json();

      if (data.success) {
        // 成功：關閉彈窗並重定向到會員專區（Django Messages 會顯示成功訊息）
        this.closePasswordModal();
        if (data.redirect) {
          window.location.href = '/users/member/';
        }
      } else {
        // 失敗：顯示錯誤訊息
        if (data.errors) {
          this.passwordChangeErrors = data.errors;
        } else {
          this.passwordChangeErrors.general = data.message || '修改密碼失敗，請稍後再試';
        }
      }
    } catch (error) {
      console.error('修改密碼錯誤:', error);
      this.passwordChangeErrors.general = '網路錯誤，請稍後再試';
    } finally {
      this.isSubmittingPassword = false;
    }
  }
});
