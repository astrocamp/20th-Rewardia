import Alpine from "alpinejs";
import "htmx.org";
import message from './components/message.js';
import cardForm from './components/card_form.js';
import faq from './components/faq.js';
import login from './components/login.js';
import register from './components/register.js';
import subscribe from './components/subscribe.js';
import message from "./components/message.js";
import cardForm from "./components/card_form.js";
import register from "./components/register.js";
import faq from "./components/faq.js";
import login from "./components/login.js";
import subscribe from "./components/subscribe.js";


window.Alpine = Alpine;

Alpine.data("toast_fadeout", message);
Alpine.data("card_form", cardForm);
Alpine.data("register_form", register);
Alpine.data("faq_accordion", faq);
Alpine.data("login_form", login);
Alpine.data("subscribe_form", subscribe);


Alpine.start();
