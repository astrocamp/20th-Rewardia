import Alpine from "alpinejs";
import "htmx.org";

window.Alpine = Alpine;

Alpine.data("toast_fadeout", message);
Alpine.data("card_form", cardForm);
Alpine.data("register_form", register);
Alpine.data("faq_accordion", faq);
Alpine.data("login_form", login);
Alpine.data("subscribe_form", subscribe);

Alpine.start();
