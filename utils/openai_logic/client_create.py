from django.conf import settings
from openai import OpenAI

print(settings.OPENAI_API_KEY)
client = OpenAI(api_key=settings.OPENAI_API_KEY)
