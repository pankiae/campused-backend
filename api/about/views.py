from django.conf import settings
from django.core.mail import send_mail
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .models import ContactMessage
from .serializers import ContactMessageSerializer


class ContactMessageCreateView(CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        contact = serializer.save()
        send_mail(
            subject=f"New Contact Message: {contact.subject}",
            message=f"From: {contact.name}\nEmail: {contact.email}\n\n{contact.message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_NOTIFICATION_EMAIL],
        )
