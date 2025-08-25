import Alpine from "alpinejs";
import "htmx.org";

window.Alpine = Alpine;

// FAQ 頁面的 Alpine.js 功能
Alpine.data('faqAccordion', () => ({
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
Alpine.data('registerForm', () => ({
    // 密碼顯示狀態追蹤
    passwordVisible: false,
    confirmPasswordVisible: false,
    
    // 切換密碼顯示/隱藏
    togglePassword(fieldType) {
        if (fieldType === 'password') {
            this.passwordVisible = !this.passwordVisible;
        } else if (fieldType === 'confirm') {
            this.confirmPasswordVisible = !this.confirmPasswordVisible;
        }
    },
    
    // 表單提交處理
    submitForm() {
        // 目前只是先預留框架, 後續預期功能擴展(例如驗證或數據收集處理)
        console.log('表單提交處理');
    }
}));

Alpine.start();
