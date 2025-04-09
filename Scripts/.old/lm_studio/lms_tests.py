import asyncio
import lmstudio as lms

async def unload_models(identifier):
    async with lms.AsyncClient() as client:
        await asyncio.gather(
            client.llm.unload(identifier),
            client.embedding.unload(identifier)
        )

async def load_models(identifier):
    async with lms.AsyncClient() as client:
        LLM_LOAD_CONFIG = lms.LlmLoadModelConfig(seed=11434)
        await asyncio.gather(
            client.llm.load_new_instance(identifier, config=LLM_LOAD_CONFIG, ttl=None),
            client.embedding.load_new_instance(identifier, ttl=None)
        )
    
def check_loaded_models():
    # List all loaded models
    all_models = [m.identifier for m in lms.list_loaded_models()]
    print("All loaded models:", all_models)

    # List loaded embedding models
    embedding_models = [m.identifier for m in lms.list_loaded_models("embedding")]
    print("Loaded embedding models:", embedding_models)

    # List loaded LLMs
    llms = [m.identifier for m in lms.list_loaded_models("llm")]
    print("Loaded LLMs:", llms)


async def python_load_model(identify, model_name):
    async with lms.AsyncClient() as client:
        existing_models = [m.identifier for m in lms.list_loaded_models("llm")]
        if model_name not in existing_models:
            await asyncio.gather(
                client.llm.load_new_instance(identify, model_name, ttl=60*90),
            )
        else:
             await asyncio.gather(
                client.llm.unload(model_name)
            )


def unload_python_sdk_model(model_name):
    loaded_models = [m.identifier for m in lms.list_loaded_models("llm")]
    for model in loaded_models:
        if model_name in model:
            lms.llm(model).unload()
            print(f"Model {model} is unloaded.")

if __name__ == "__main__":
    model_id = "qwen2.5-0.5b-instruct"
    instance_name = "Default Chat"
    time_to_live = 60*90
    #
    # lms.llm(model_id, ttl=time_to_live)
    load_client = lms.get_default_client()

    #  do something random on the loading progress
    load_client.llm.load_new_instance(model_id, instance_identifier=instance_name, ttl=time_to_live, on_load_progress=)
    # asyncio.run(python_load_model("qwen2.5-0.5b-instruct", "Default Chat"))
    # asyncio.run(python_load_model("qwen2.5-0.5b-instruct", "Default Chad"))
    # asyncio.run(python_load_model("llama-3.2-1b-instruct", "Default"))
    # asyncio.run(python_load_model("qwen2.5-0.5b-instruct", "random dude!"))
    # print("Model loaded")
    # asyncio.run(unload_python_sdk_model("D*"))
    # check_loaded_models()  
    # asyncio.run(load_models("qwen2.5-0.5b-instruct"))
    # asyncio.run(unload_models("qwen2.5-0.5b-instruct"))