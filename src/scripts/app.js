import Alpine from 'alpinejs';
import 'htmx.org';

import faq from './components/faq.js';
import login from './components/login.js';
import register from './components/register.js';
import subscribe from './components/subscribe.js';

window.Alpine = Alpine;

Alpine.data('faq_accordion', faq);
Alpine.data('login_form', login);
Alpine.data('register_form', register);
Alpine.data('subscribe_form', subscribe);

Alpine.start();
