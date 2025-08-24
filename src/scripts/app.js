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
    togglePassword(fieldId) {
        const field = document.getElementById(fieldId);
        const button = field.nextElementSibling;
        const icon = button.querySelector('svg');
        
        if (field.type === 'password') {
            field.type = 'text';
            // 顯示隱藏圖標
            icon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"/>
            `;
        } else {
            field.type = 'password';
            // 顯示眼睛圖標
            icon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            `;
        }
    },
    
    // 表單提交處理
    submitForm() {
        // 這裡可以添加表單驗證邏輯
        console.log('表單提交處理');
    }
}));

Alpine.start();
