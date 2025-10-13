import os

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context, Template


def _send_html_email(
    subject: str, template_filename: str, context: dict, recipient_email: str
):
    """
    Load an HTML template from auth/../render_files/<template_filename>, render it with `context`,
    and send it via Gmail SMTP (as configured in settings.py).
    """
    # 1) Locate the template file under utils/files/
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(utils_dir, "../render_files", template_filename)

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Email template not found at {template_path}")

    # 2) Render the template
    template = Template(template_content)
    html_body = template.render(Context(context))

    # 3) Construct & send the EmailMessage
    email_message = EmailMessage(
        subject=subject,
        body=html_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email_message.content_subtype = "html"  # mark this email as HTML
    email_message.send(fail_silently=False)
