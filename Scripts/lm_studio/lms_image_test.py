import lmstudio as lms
from lmstudio._sdk_models import ChatMessagePartFileData, ChatMessagePartTextData, ChatMessageDataUser

def run_test():
    image_path = r"C:\Users\jaron\OneDrive\Pictures\Screenshots\Screenshot 2025-04-11 130930.png"
    image_handle = lms.prepare_image(image_path)
    image_handle
    ChatMessagePartFileData(name='Screenshot 2025-04-11 130930.png', identifier='1744382888136 - 650.png', size_bytes=220730, file_type='image')
    llm = lms.llm("qwen2-vl-2b-instruct")
    chat = lms.Chat()
    chat.add_user_message("Describe this image please", images=[image_handle])
    ChatMessageDataUser(content=[ChatMessagePartTextData(text='Describe this image please'), ChatMessagePartFileData(name='Screenshot 2025-04-11 130930.png', identifier='1744382888136 - 650.png', size_bytes=220730, file_type='image')])
    prediction = llm.respond(chat)
    print(prediction)


run_test()