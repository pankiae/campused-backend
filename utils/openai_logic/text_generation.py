from utils.openai_logic.client_create import client


def text_generation(q):  # q = query
    response = client.responses.create(model="gpt-5-nano-2025-08-07", input=q)
    return response.output_text
