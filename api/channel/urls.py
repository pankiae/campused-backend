from django.urls import path

import api.channel.views as V

urlpatterns = [
    path("", view=V.ChannelView.as_view(), name="channel-create"),
    path("list-channels", view=V.ListChannelView.as_view(), name="get-channels"),
    path("<uuid:channel_id>", view=V.PatchChannelView.as_view(), name="channel-patch"),
    path(
        "<uuid:channel_id>/file/<str:file_name>",
        V.FileFetchView.as_view(),
        name="fetch-file",
    ),
    path("exam-generation", V.GenerateExamAPIView.as_view(), name="exam-generation"),
    path("list-exams", V.ListExamView.as_view(), name="list-exams"),
    path("exam/<uuid:exam_id>", view=V.GetExamView.as_view(), name="exam"),
]
