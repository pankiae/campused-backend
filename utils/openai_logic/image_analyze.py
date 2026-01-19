import base64

from utils.openai_logic.client_create import client


def convert_byte_image2base64(image_file_bytes):
    data = image_file_bytes.read()
    image_file_bytes.seek(0)
    return base64.b64encode(data).decode("utf-8")


def image_analyze(image_file_bytes):
    base64_image = convert_byte_image2base64(image_file_bytes)
    res = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Analyze all details of this image, if it's photo of the document then transcribe it and if the diagram or anything than explain it.",
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )
    return res.output_text
