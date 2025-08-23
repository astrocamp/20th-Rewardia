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

Alpine.start();
