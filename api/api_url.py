from django.urls import include, path

urlpatterns = [
    path("auth/", include("api.user.urls")),
    path("chat/", include("api.chat.urls")),
]
