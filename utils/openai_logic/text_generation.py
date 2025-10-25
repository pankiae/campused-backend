from utils.openai_logic.client_create import client


def text_generation(conversation: list):
    response = client.responses.create(
        model="gpt-5-nano-2025-08-07", input=conversation
    )
    return response.output_text
