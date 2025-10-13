import os

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.file_logic import file_loader
from utils.openai_logic import image_analyze, text_generation

from .models import Channel
from .serializers import ChannelListSerializer

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/webp",
]


# Create your views here.
class ChannelView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        uploaded_files = request.FILES.getlist("files")
        query = request.data.get("q")
        if not uploaded_files and not query:
            return Response(
                {"error": "No files or query provided"}, status=400
            )  # 400 Bad Request
        conversation = [
            {
                "role": "system",
                "content": "You are a Exam Preparation helpful assistant. You help students to prepare for their exams by providing them with relevant information and resources. You can also help them to create study plans and schedules. You are very friendly and always respond in a positive manner. You can provide the answer directly or MCQ questions if the user asks for it or on your own for their better clarity about the topics.",
            }
        ]
        print(f"Received {len(uploaded_files)} files and query: {query}")
        for file in uploaded_files:
            if file.content_type not in ALLOWED_TYPES:
                return Response(
                    {"error": f"File type {file.content_type} not allowed"}, status=400
                )

            ext = os.path.splitext(file.name)[1].lower().strip(".")
            print(f"Processing file: {file.name} with extension: {ext}")

            if ext in ["jpg", "jpeg", "png", "webp"]:
                print("Processing image file:", file.name)
                image_transcribe: str = image_analyze.image_analyze(file)
                print("Extracted text from image:\n", image_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the image that user shared"
                        + image_transcribe,
                    }
                )

            elif ext in ["docx", "pdf"]:
                print("Processing document file:", file.name)
                docx_transcribe = file_loader.read_file(file.file)
                print("Extracted text from document:\n", docx_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the document that user shared:\n\n"
                        + docx_transcribe,
                    }
                )

        if query:
            res = text_generation.text_generation(
                conversation + [{"role": "user", "content": query}]
            )
            conversation.append(
                {"role": "assistant", "content": res},
            )

        Channel.objects.create(
            user=request.user, title="new chat", context=conversation
        )
        print("Conversation so far:\n", conversation)

        return Response(
            {"conversation": conversation},
            status=201,  # 201 Created is often used for successful POST requests
        )


class ListChannelView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChannelListSerializer

    def get_queryset(self):
        return Channel.objects.filter(user=self.request.user)


class PatchChannelView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, channel_id):
        conversation = Channel.objects.get(id=channel_id, user=request.user)
        return Response(
            {"conversation": conversation.context},
            status=status.HTTP_200_OK,
        )

    def post(self, request, channel_id):
        try:
            conversation = Channel.objects.get(id=channel_id, user=request.user)
        except Channel.DoesNotExist:
            return Response(
                {"error": "Channel not found"}, status=status.HTTP_404_NOT_FOUND
            )
