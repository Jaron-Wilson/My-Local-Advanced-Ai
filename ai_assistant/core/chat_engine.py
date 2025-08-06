import json
from openai import OpenAI
from ai_assistant.config import MODEL, BASE_URL, API_KEY
from ai_assistant.tools.tool_registry import load_tools

class ChatEngine:
    def __init__(self):
        self.client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
        self.tools, self.tool_functions = load_tools()
        self.messages = []
        self.pending_image_query = None

    def process_stream(self, stream, add_assistant_label=True):
        """Handle streaming responses from the API"""
        collected_text = ""
        tool_calls = []
        first_chunk = True

        for chunk in stream:
            delta = chunk.choices[0].delta

            # Handle regular text output
            if delta.content:
                if first_chunk:
                    print()
                    if add_assistant_label:
                        print("Assistant:", end=" ", flush=True)
                    first_chunk = False
                print(delta.content, end="", flush=True)
                collected_text += delta.content

            # Handle tool calls
            elif delta.tool_calls:
                for tc in delta.tool_calls:
                    if len(tool_calls) <= tc.index:
                        tool_calls.append({
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        })

                    tool_calls[tc.index] = {
                        "id": (tool_calls[tc.index]["id"] + (tc.id or "")),
                        "type": "function",
                        "function": {
                            "name": (tool_calls[tc.index]["function"]["name"] + (tc.function.name or "")),
                            "arguments": (tool_calls[tc.index]["function"]["arguments"] + (tc.function.arguments or ""))
                        }
                    }

        return collected_text, tool_calls

    def start_chat(self):
        print("Assistant: Hi! I am an AI agent empowered with various tools including web browsing. (Type 'quit' to exit)")

        while True:
            user_input = input("\nYou: ").strip()

            if user_input.lower() == "quit":
                break

            # Handle pending image override confirmation
            if self.pending_image_query:
                if user_input.lower() in ['yes', 'y']:
                    result = self.tool_functions["google_image_search"](self.pending_image_query["query"], override=True)
                    self.messages.append({
                        "role": "tool",
                        "content": str(result),
                        "tool_call_id": self.pending_image_query["tool_call_id"]
                    })
                elif user_input.lower() in ['no', 'n']:
                    result = self.tool_functions["google_image_search"](self.pending_image_query["query"], override=False)
                    self.messages.append({
                        "role": "tool",
                        "content": str(result),
                        "tool_call_id": self.pending_image_query["tool_call_id"]
                    })
                self.pending_image_query = None
                continue

            self.messages.append({"role": "user", "content": user_input})

            # Get initial response
            response_text, tool_calls = self.process_stream(
                self.client.chat.completions.create(
                    model=MODEL,
                    messages=self.messages,
                    tools=self.tools,
                    stream=True,
                    temperature=0.2
                )
            )

            if not tool_calls:
                print()

            text_in_first_response = len(response_text) > 0
            if text_in_first_response:
                self.messages.append({"role": "assistant", "content": response_text})

            # Handle tool calls if any
            if tool_calls:
                tool_name = tool_calls[0]["function"]["name"]
                print()
                if not text_in_first_response:
                    print("Assistant:", end=" ", flush=True)
                print(f"**Calling Tool: {tool_name}**")

                self.messages.append({"role": "assistant", "tool_calls": tool_calls})

                # Execute tool calls
                for tool_call in tool_calls:
                    try:
                        function_name = tool_call["function"]["name"]
                        function_args = json.loads(tool_call["function"]["arguments"])

                        if function_name in self.tool_functions:
                            result = self.tool_functions[function_name](**function_args)
                        else:
                            result = {"error": f"Tool {function_name} not found."}

                    except json.JSONDecodeError:
                        result = {"error": "Invalid JSON arguments."}
                        continue

                    if isinstance(result, dict) and result.get("status") == "confirm_override":
                        print("\nAssistant: There are existing images. Would you like to override them? (yes/no)")
                        self.pending_image_query = {
                            "query": result["query"],
                            "tool_call_id": tool_call["id"]
                        }
                        continue

                    self.messages.append({
                        "role": "tool",
                        "content": str(result),
                        "tool_call_id": tool_call["id"]
                    })

                # If we didn't have a pending image query, get final response after tool execution
                if not self.pending_image_query:
                    final_response, _ = self.process_stream(
                        self.client.chat.completions.create(
                            model=MODEL,
                            messages=self.messages,
                            stream=True
                        ),
                        add_assistant_label=False
                    )

                    if final_response:
                        print()
                        self.messages.append({"role": "assistant", "content": final_response})
