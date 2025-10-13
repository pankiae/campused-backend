from django.urls import path

import api.channel.views as V

urlpatterns = [
    path("", view=V.ChannelView.as_view(), name="channel-create"),
    path("list-channels", view=V.ListChannelView.as_view(), name="get-channels"),
    path("<uuid:channel_id>", view=V.PatchChannelView.as_view(), name="channel-patch"),
]
