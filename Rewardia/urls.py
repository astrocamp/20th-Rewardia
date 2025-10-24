from debug_toolbar.toolbar import debug_toolbar_urls
from django.urls import path, include
from apps.pages.context_processors import STATIC_VERSION_HASH

handler404 = 'apps.pages.views.custom_404'

urlpatterns = [
    path("", include("apps.pages.urls")),
    path("users/", include("apps.users.urls")),
    path("sessions/", include("apps.sessions.urls")),
    path(f"{STATIC_VERSION_HASH}/", include("apps.admins.urls")),
    path("api/", include("apps.ext_api.urls")),
    path("api/chatbot/", include("apps.chatbot.urls")),  # Gemini URLs(AI robot)
    path("accounts/", include("allauth.urls")),  # allauth URLs(Google 登入)
] + debug_toolbar_urls()
