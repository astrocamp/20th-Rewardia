import Alpine from 'alpinejs';
import "htmx.org";

// Import all components
import mainSearchComponent from './components/main.js';
import cardFormComponent from './components/card_form.js';
import faqComponent from './components/faq.js';
import loginComponent from './components/login.js';
import messageComponent from './components/message.js';
import registerComponent from './components/register.js';
import subscribeComponent from './components/subscribe.js';

window.Alpine = Alpine;

// Register all components
Alpine.data('main_search', mainSearchComponent);
Alpine.data('card_form', cardFormComponent);
Alpine.data('faq_accordion', faqComponent);
Alpine.data('login_form', loginComponent);
Alpine.data('register_form', registerComponent);
Alpine.data('subscribe_form', subscribeComponent);
Alpine.data("toast_fadeout", messageComponent);

Alpine.start();
