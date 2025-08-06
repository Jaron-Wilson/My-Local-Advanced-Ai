import os
import importlib

def load_tools():
    tools = []
    tool_functions = {}

    tools_dir = os.path.dirname(__file__)
    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"ai_assistant.tools.{filename[:-3]}"
            module = importlib.import_module(module_name)

            if hasattr(module, "tools"):
                tools.extend(module.tools)

            if hasattr(module, "tool_functions"):
                tool_functions.update(module.tool_functions)

    return tools, tool_functions
