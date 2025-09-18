import Alpine from "alpinejs";
import "htmx.org";

// Import all components
import './components/header.js';
import './components/calculator.js';
import './components/rewards.js';
import chatbot from "./components/chatbot.js";
import mainSearchComponent from './components/main.js';
import cardFormComponent from './components/card_form.js';
import faqComponent from './components/faq.js';
import loginComponent from './components/login.js';
import messageComponent from './components/message.js';
import registerComponent from './components/register.js';
import subscribeComponent from './components/subscribe.js';
import imageUploadComponent from './components/image_upload.js';
import schedulerComponent from './components/scheduler.js';
import cardCameraComponent from './components/card_camera.js';
import passwordChangeComponent from './components/password_change.js';
import memberZoneComponent from './components/member_zone.js';

window.Alpine = Alpine;

// 全域 toast 函數
window.showToast = function(message, type = 'info') {
  // 創建 toast 資料
  const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  const toastData = {
    id: toastId,
    message,
    type,
    visible: true
  };
  
  // 觸發自定義事件，讓頁面處理 toast 顯示
  window.dispatchEvent(new CustomEvent('show-toast', { 
    detail: toastData 
  }));
};

Alpine.data("main_search", mainSearchComponent);
Alpine.data("card_form", cardFormComponent);
Alpine.data("faq_accordion", faqComponent);
Alpine.data("login_form", loginComponent);
Alpine.data("register_form", registerComponent);
Alpine.data("subscribe_form", subscribeComponent);
Alpine.data("toast_fadeout", messageComponent);
Alpine.data("chatbot", chatbot);
Alpine.data("imageUpload", imageUploadComponent);
Alpine.data("schedulerControl", schedulerComponent);
Alpine.data("card_camera", cardCameraComponent);
Alpine.data("password_change", passwordChangeComponent);
Alpine.data("member_zone", memberZoneComponent);

// Toast 組件
Alpine.data("member_zone_toast", () => ({
  toasts: [],
  addToast(detail) {
    this.toasts.push(detail);
    // 3 秒後自動移除
    setTimeout(() => this.removeToast(detail.id), 3000);
  },
  removeToast(id) {
    this.toasts = this.toasts.filter(t => t.id !== id);
  }
}));

Alpine.start();
