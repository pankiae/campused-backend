from django.urls import include, path

urlpatterns = [
    path("auth/", include("api.user.urls")),
    path("channel/", include("api.channel.urls")),
    path("subscriptions/", include("api.subscriptions.urls")),
]
