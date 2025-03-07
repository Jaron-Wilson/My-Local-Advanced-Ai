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



if __name__ == "__main__":
    check_loaded_models()  
    # asyncio.run(load_models("qwen2.5-0.5b-instruct"))
    # asyncio.run(unload_models("qwen2.5-0.5b-instruct"))