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

Alpine.start();
