from utils.openai_logic.client_create import client


def text_generation(conversation: list, model="gpt-4.1-mini"):
    res = client.responses.create(model=model, input=conversation)

    return res.output_text, res.usage.input_tokens, res.usage.output_tokens


def title_generation(user_input, model="gpt-4.1-mini"):
    conversation = [
        {
            "role": "system",
            "content": " you are title generation assistant. You have to generate the title on the basis of the user inputs. User may ask about the question, random issues, techincal guide, or study related tips. No matter whatever the  user input is, you just have to generate the title of that input in just 3-4 words. And that title will repersent the upcoming conversation on that user inputs. Basically User is giving the input in the ai chat conversation app, so you have to give the title for that chat.",
        },
        {"role": "user", "content": user_input},
        {
            "role": "system",
            "content": "As you have seen the user inputs above, so on the basis of the user input, generate the title of the conversation in just 3-4 words only.",
        },
    ]
    res = client.responses.create(model=model, input=conversation)

    return res.output_text, res.usage.input_tokens, res.usage.output_tokens
