import os

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.openai_logic import image_analyze, text_generation

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/webp",
]


# Create your views here.
class Channel(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        uploaded_files = request.FILES.getlist("files")
        query = request.data.get("q")

        conversation = []

        for file in uploaded_files:
            if file.content_type not in ALLOWED_TYPES:
                return Response(
                    {"error": f"File type {file.content_type} not allowed"}, status=400
                )
            ext = os.path.splitext(file.name)[1].lower().strip(".")

            if ext in ["jpg", "jpeg", "png", "webp"]:
                image_transcribe: str = image_analyze.image_analyze(file)
                conversation.append(
                    {
                        "role": "assistant",
                        "content": "This is the information that I have extracted from the image that user shared"
                        + image_transcribe,
                    }
                )

            # if ext in ["docx", "doc"]:
            #     docx_transcribe =
            print(file.name, file.content_type, file.size)
        res = text_generation.text_generation(query)

        return Response(
            {"detail": conversation},
            status=201,  # 201 Created is often used for successful POST requests
        )
