from utils.openai_logic.client_create import client


def text_generation(conversation: list, model="gpt-4.1-mini"):
    res = client.responses.create(model=model, input=conversation)

    return res.output_text, res.usage.input_tokens, res.usage.output_tokens
