// Related HTML: templates/users/login.html
export default () => ({
  passwordVisible: false,
  
  togglePassword() {
    this.passwordVisible = !this.passwordVisible;
  },
});