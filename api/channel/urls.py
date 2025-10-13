from django.urls import path

import api.channel.views as V

urlpatterns = [
    path("", view=V.ChannelView.as_view(), name="channel-create"),
    path("get-channels", view=V.ChannelListView.as_view(), name="get-channels"),
    path("<uuid:channel_id>", view=V.ChannelPatchView.as_view(), name="channel-patch")
    ]
