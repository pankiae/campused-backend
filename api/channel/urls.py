from django.urls import path

import api.channel.views as V

urlpatterns = [path("", view=V.ChannelView.as_view(), name="channel-create")]
