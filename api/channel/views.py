import copy
import logging
import os

from django.conf import settings
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.file_logic import file_loader
from utils.openai_logic import image_analyze, text_generation, token_calculation

from .models import Channel
from .serializers import ChannelListSerializer

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/webp",
]

# Limit uploads to 10 MB per file by default; can be overridden in Django settings
MAX_FILE_SIZE = getattr(settings, "MAX_UPLOAD_FILE_SIZE", 20 * 1024 * 1024)

logger = logging.getLogger(__name__)


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

        gather_tokens = {"input": 0, "output": 0}
        select_openai_model = "gpt-4.1-mini"

        logger.info("Received %d files and query: %s", len(uploaded_files), query)
        for file in uploaded_files:
            if file.content_type not in ALLOWED_TYPES:
                return Response(
                    {"error": f"File type {file.content_type} not allowed"}, status=400
                )

            ext = os.path.splitext(file.name)[1].lower().strip(".")
            logger.debug("Processing file: %s with extension: %s", file.name, ext)

            # Basic file size check
            try:
                size = getattr(file, "size", None)
                if size is not None and size > MAX_FILE_SIZE:
                    logger.warning(
                        "File %s exceeds max size (%d > %d)",
                        file.name,
                        size,
                        MAX_FILE_SIZE,
                    )
                    return Response({"error": "File too large"}, status=400)
            except Exception:
                # don't fail the whole request if size can't be determined
                logger.debug(
                    "Could not determine file size for %s", file.name, exc_info=True
                )
            if ext in ["jpg", "jpeg", "png", "webp"]:
                logger.debug("Processing image file: %s", file.name)
                try:
                    image_transcribe, image_input_tokens, image_output_tokens = (
                        image_analyze.image_analyze(file, select_openai_model)
                    )
                    gather_tokens["input"] += image_input_tokens
                    gather_tokens["output"] += image_output_tokens
                except Exception:
                    logger.exception("Failed to analyze image: %s", file.name)
                    return Response(
                        {"error": "Failed to process image file"}, status=500
                    )
                logger.debug("Extracted text from image: %s", image_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the image that user shared: \n"
                        + image_transcribe,
                    }
                )

            elif ext in ["docx", "pdf"]:
                logger.debug("Processing document file: %s", file.name)
                try:
                    docx_transcribe = file_loader.read_file(file.file)
                except Exception:
                    logger.exception("Failed to read document: %s", file.name)
                    return Response(
                        {"error": "Failed to process document file"}, status=500
                    )
                logger.debug("Extracted text from document: %s", docx_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the document that user shared:\n\n"
                        + docx_transcribe,
                    }
                )

        if query:
            try:
                sorted_conversation = remove_file_name_conversation(conversation)
                res, text_input_tokens, text_output_tokens = (
                    text_generation.text_generation(
                        sorted_conversation + [{"role": "user", "content": query}],
                        select_openai_model,
                    )
                )
                gather_tokens["input"] += text_input_tokens
                gather_tokens["output"] += text_output_tokens
            except Exception:
                logger.exception("Text generation failed for query: %s", query)
                return Response({"error": "Failed to generate text"}, status=500)

            user_query = {"role": "user", "content": query}
            if uploaded_files:
                user_query["files"] = [f.name for f in uploaded_files]
            query_res = {"role": "assistant", "content": res}
            conversation.extend([user_query, query_res])

        gather_tokens_cost_sum = token_calculation.sum_input_output_token_cost(
            select_openai_model, gather_tokens["input"], gather_tokens["output"]
        )
        channnel = Channel.objects.create(
            user=request.user,
            title=request.data.get("title", "new chat"),
            context=conversation,
            token_cost=gather_tokens_cost_sum,
        )
        logger.info(
            "Conversation saved for user %s (messages=%d)",
            request.user,
            len(conversation),
        )

        return Response(
            {
                "conversation": conversation,
                "channel_id": channnel.id,
            },
            status=201,  # 201 Created is often used for successful POST requests
        )


class ListChannelView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChannelListSerializer

    def get_queryset(self):
        return Channel.objects.filter(user=self.request.user).order_by("-updated_at")


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
        uploaded_files = request.FILES.getlist("files")
        query = request.data.get("q")
        if not uploaded_files and not query:
            return Response(
                {"error": "No files or query provided"}, status=400
            )  # 400 Bad Request
        try:
            channel = Channel.objects.get(id=channel_id, user=request.user)
            conversation = channel.context
            logger.info("conversation: %s", conversation)
        except Channel.DoesNotExist:
            return Response(
                {"error": "Channel not found"}, status=status.HTTP_404_NOT_FOUND
            )
        logger.info(
            "Patching channel %s: received %d files and query: %s",
            channel_id,
            len(uploaded_files),
            query,
        )

        for file in uploaded_files:
            if file.content_type not in ALLOWED_TYPES:
                return Response(
                    {"error": f"File type {file.content_type} not allowed"}, status=400
                )

            ext = os.path.splitext(file.name)[1].lower().strip(".")
            logger.debug("Processing file: %s with extension: %s", file.name, ext)

            # Basic file size check
            try:
                size = getattr(file, "size", None)
                if size is not None and size > MAX_FILE_SIZE:
                    logger.warning(
                        "File %s exceeds max size (%d > %d)",
                        file.name,
                        size,
                        MAX_FILE_SIZE,
                    )
                    return Response({"error": "File too large"}, status=400)
            except Exception:
                logger.debug(
                    "Could not determine file size for %s", file.name, exc_info=True
                )

            if ext in ["jpg", "jpeg", "png", "webp"]:
                logger.debug("Processing image file: %s", file.name)
                try:
                    image_transcribe: str = image_analyze.image_analyze(file)
                except Exception:
                    logger.exception("Failed to analyze image: %s", file.name)
                    return Response(
                        {"error": "Failed to process image file"}, status=500
                    )
                logger.debug("Extracted text from image: %s", image_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the image that user shared: \n"
                        + image_transcribe,
                    }
                )

            elif ext in ["docx", "pdf"]:
                logger.debug("Processing document file: %s", file.name)
                try:
                    docx_transcribe = file_loader.read_file(file.file)
                except Exception:
                    logger.exception("Failed to read document: %s", file.name)
                    return Response(
                        {"error": "Failed to process document file"}, status=500
                    )
                logger.debug("Extracted text from document: %s", docx_transcribe)
                conversation.append(
                    {
                        "role": "system",
                        "content": "This is the information that I have extracted from the document that user shared:\n\n"
                        + docx_transcribe,
                    }
                )
        if query:
            try:
                sorted_conversation = remove_file_name_conversation(conversation)
                res = text_generation.text_generation(
                    sorted_conversation + [{"role": "user", "content": query}]
                )
            except Exception:
                logger.exception("Text generation failed for query: %s", query)
                return Response({"error": "Failed to generate text"}, status=500)

            user_query = {"role": "user", "content": query}
            if uploaded_files:
                user_query["files"] = [f.name for f in uploaded_files]
            query_res = {"role": "assistant", "content": res}
            conversation.extend([user_query, query_res])

        channel.context = conversation
        channel.save()
        logger.info(
            "Updated channel %s for user %s (messages=%d)",
            channel_id,
            request.user,
            len(conversation),
        )

        return Response(
            {"conversation": conversation},
            status=200,
        )


def remove_file_name_conversation(conversation):
    new_conversation = []
    for message in conversation:
        msg_copy = copy.deepcopy(message)
        msg_copy.pop("files", None)
        new_conversation.append(msg_copy)
    return new_conversation
