from openai import OpenAI
import base64

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

path = input("Enter a local filepath to an image: ")

try:
    with open(path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
except IOError:
    print("Couldn't read the image. Make sure the path is correct and the file exists.")
    exit()

completion = client.chat.completions.create(
  model="model-identifier",
  messages=[
    {
      "role": "system",
      "content": "You are an AI assistant that analyzes images.",
    },
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What's in this image?"},
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
          },
        },
      ],
    }
  ],
  max_tokens=1000,
  stream=True
)

for chunk in completion:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)