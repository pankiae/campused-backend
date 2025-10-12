from django.urls import path

import api.channel.views as V

urlpatterns = [path("channel", view=V.Channel.as_view(), name="channel")]
