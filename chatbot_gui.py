import tkinter as tk
from tkinter import scrolledtext, Menu, Toplevel, StringVar, Label, Entry, Button, Frame, messagebox
import json
import os
from openai import OpenAI # For OpenAI client initialization

CONFIG_FILE = "chatbot_config.json"

# --- Dummy Tool Functions (for testing config values) ---
def get_weather(location, gui_instance=None): # gui_instance to access self.config
    api_key_to_use = "Not configured"
    if gui_instance and gui_instance.config.get("weather_api_key"):
        api_key_to_use = gui_instance.config["weather_api_key"]
    elif os.getenv("WEATHER_API_KEY"): # Fallback to environment variable
        api_key_to_use = os.getenv("WEATHER_API_KEY")
    
    if api_key_to_use == "Not configured" or not api_key_to_use:
        return {"error": "Weather API Key not configured."}
    # Mask the API key for display
    masked_key = f"{'*' * (len(api_key_to_use) - 4)}{api_key_to_use[-4:]}" if len(api_key_to_use) > 4 else api_key_to_use
    return {"info": f"Simulated weather for {location} using key: {masked_key}"}

def get_weather_forecast(location, gui_instance=None):
    api_key_to_use = "Not configured"
    if gui_instance and gui_instance.config.get("weather_api_key"):
        api_key_to_use = gui_instance.config["weather_api_key"]
    elif os.getenv("WEATHER_API_KEY"):
        api_key_to_use = os.getenv("WEATHER_API_KEY")

    if api_key_to_use == "Not configured" or not api_key_to_use:
        return {"error": "Weather API Key not configured."}
    masked_key = f"{'*' * (len(api_key_to_use) - 4)}{api_key_to_use[-4:]}" if len(api_key_to_use) > 4 else api_key_to_use
    return {"info": f"Simulated forecast for {location} using key: {masked_key}"}

class ChatbotGUI:
    def __init__(self, master, config_filepath=CONFIG_FILE, run_gui_setup=True): # Added config_filepath and run_gui_setup
        self.master = master 
        self.config_filepath = config_filepath 
        
        if master and run_gui_setup: 
            master.title("Chatbot GUI")
            master.geometry("600x500") 
            # master.minsize(550, 450) # Min size can be set in _setup_ui if needed

        self.config = {} 
        self._load_config() 

        try:
            self.client = OpenAI(base_url=self.config.get('base_url'), api_key="lm-studio") 
        except Exception as e:
            if master and run_gui_setup: # Only show messagebox if GUI is running
                messagebox.showerror("OpenAI Client Init Error", f"Failed to initialize OpenAI client with URL '{self.config.get('base_url')}': {e}\nPlease check the Base URL in File > Settings.\nUsing a default placeholder URL.", parent=master if master.winfo_exists() else None)
            self.config['base_url'] = "http://127.0.0.1:1234/v1" 
            self.client = OpenAI(base_url=self.config['base_url'], api_key="lm-studio") 
            
        self.MODEL = self.config.get('model_name')
        
        # GUI specific attributes, only if master is present
        if master and run_gui_setup:
            self._assistant_prefix_displayed_this_turn = False
            self.messages = [] # This would be for full chat history, might not be needed just for config tests
            self.gui_queue = queue.Queue() # If other parts of GUI use it
            self.worker_thread = None # If other parts of GUI use it
            self.send_button_enabled = True # If other parts of GUI use it

            master.protocol("WM_DELETE_WINDOW", self._on_closing) # Renamed from master.quit
            self._setup_ui(master)
        elif master is None: # For testing config logic without full GUI
            self.status_bar = MockStatusBar() # Use mock for tests

    def _setup_ui(self, master): # Setup UI elements
        menubar = Menu(master)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Settings...", command=self._open_settings_dialog)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self._on_closing) 
        menubar.add_cascade(label="File", menu=filemenu)
        master.config(menu=menubar)

        self.chat_history = scrolledtext.ScrolledText(master, state='disabled', wrap=tk.WORD, height=15)
        self.chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_history.tag_configure("bold", font=("TkDefaultFont", 9, "bold"))

        self.user_input_entry = Entry(master) 
        self.user_input_entry.pack(padx=10, pady=(0, 5), fill=tk.X, expand=False)
        self.user_input_entry.bind("<Return>", self.send_message_event)

        self.send_button = Button(master, text="Send", command=self.send_message_action)
        self.send_button.pack(padx=10, pady=(0, 10), fill=tk.X, expand=False)

        self.status_bar = Label(master, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _load_config(self):
        defaults = {
            "base_url": "http://127.0.0.1:1234/v1",
            "model_name": "qwen2.5-7b-instruct-1m", 
            "weather_api_key": "" 
        }
        if os.path.exists(self.config_filepath):
            try:
                with open(self.config_filepath, 'r') as f:
                    loaded_config = json.load(f)
                self.config = {key: loaded_config.get(key, defaults[key]) for key in defaults}
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading or parsing {self.config_filepath}: {e}. Using defaults.")
                self.config = defaults.copy()
                if self.master and self.master.winfo_exists():
                     messagebox.showwarning("Config Warning", f"Error loading '{self.config_filepath}': {e}.\nUsing default settings.", parent=self.master)
                self._save_config() 
        else:
            if hasattr(self, 'master') and self.master: # Only print if master exists (not in test setup without master)
                 print(f"{self.config_filepath} not found. Creating with defaults.")
            self.config = defaults.copy()
            self._save_config() 
        
        for key, value in defaults.items():
            if key not in self.config or self.config[key] is None: 
                self.config[key] = value

    def _save_config(self):
        try:
            with open(self.config_filepath, 'w') as f:
                json.dump(self.config, f, indent=4)
            if hasattr(self, 'status_bar') and self.status_bar and isinstance(self.status_bar, tk.Label): # Check if status_bar is a Tkinter Label
                self.status_bar.config(text="Configuration saved successfully.")
            elif hasattr(self.status_bar, 'text'): # For MockStatusBar
                self.status_bar.text = "Configuration saved successfully."
        except IOError as e:
            if hasattr(self, 'status_bar') and self.status_bar and isinstance(self.status_bar, tk.Label):
                 self.status_bar.config(text=f"Error saving configuration: {e}")
            elif hasattr(self.status_bar, 'text'):
                 self.status_bar.text = f"Error saving configuration: {e}"
            if hasattr(self, 'master') and self.master and self.master.winfo_exists():
                 messagebox.showerror("Config Save Error", f"Could not save configuration to {self.config_filepath}:\n{e}", parent=self.master)

    def _open_settings_dialog(self):
        settings_dialog = Toplevel(self.master)
        settings_dialog.title("Settings")
        settings_dialog.geometry("500x180")
        settings_dialog.transient(self.master)
        settings_dialog.grab_set()

        current_config = self.config 

        Label(settings_dialog, text="LM Studio Base URL:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        url_var = StringVar(value=current_config.get("base_url", ""))
        Entry(settings_dialog, textvariable=url_var, width=50).grid(row=0, column=1, padx=10, pady=5)

        Label(settings_dialog, text="Model Name:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        model_var = StringVar(value=current_config.get("model_name", ""))
        Entry(settings_dialog, textvariable=model_var, width=50).grid(row=1, column=1, padx=10, pady=5)

        Label(settings_dialog, text="Weather API Key:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        weather_key_var = StringVar(value=current_config.get("weather_api_key", ""))
        Entry(settings_dialog, textvariable=weather_key_var, width=50).grid(row=2, column=1, padx=10, pady=5)
        
        def on_save():
            new_base_url = url_var.get().strip()
            new_model_name = model_var.get().strip()
            url_changed = self.config.get("base_url") != new_base_url
            
            self.config["base_url"] = new_base_url
            self.config["model_name"] = new_model_name
            self.config["weather_api_key"] = weather_key_var.get().strip()
            self._save_config()
            self.MODEL = self.config["model_name"]
            
            if url_changed:
                try:
                    self.client = OpenAI(base_url=self.config["base_url"], api_key="lm-studio")
                    message = "Settings saved. OpenAI client re-initialized."
                    self.status_bar.config(text=message)
                    messagebox.showinfo("Settings Saved", message, parent=settings_dialog)
                except Exception as e:
                    error_message = f"Failed to re-initialize OpenAI client: {e}"
                    self.status_bar.config(text=error_message)
                    messagebox.showerror("Client Error", error_message, parent=settings_dialog)
            else:
                self.status_bar.config(text="Settings saved successfully.") 
                messagebox.showinfo("Settings Saved", "Settings saved successfully.", parent=settings_dialog)
            settings_dialog.destroy()

        button_frame = Frame(settings_dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10) 
        Button(button_frame, text="Save", command=on_save, width=10).pack(side=tk.LEFT, padx=10)
        Button(button_frame, text="Cancel", command=settings_dialog.destroy, width=10).pack(side=tk.RIGHT, padx=10)
        settings_dialog.wait_window()

    def send_message_event(self, event=None): self.send_message_action()

    def send_message_action(self): # Placeholder - full logic to be re-integrated later
        user_text = self.user_input_entry.get() 
        if not user_text.strip(): return
        self.display_message([("You: ", "bold"), (user_text, None)]) 
        self.user_input_entry.delete(0, tk.END)
        self.status_bar.config(text="Processing (placeholder)...")
        if "weather" in user_text.lower() or "forecast" in user_text.lower():
            if "forecast" in user_text.lower(): tool_output = get_weather_forecast("test_location", gui_instance=self)
            else: tool_output = get_weather("test_location", gui_instance=self)
            self.display_message([("System (Config Test): ", "bold"), (str(tool_output), None)])
        self.master.after(500, lambda: self.display_message([("Assistant: ", "bold"), ("Thinking... (LLM call not implemented yet)", None)]))
        self.master.after(1000, lambda: self.status_bar.config(text="Ready"))

    def display_message(self, message_parts, end="\n\n"):
        self.chat_history.config(state='normal')
        if isinstance(message_parts, str):
            self.chat_history.insert(tk.END, message_parts + end)
        else: 
            for part in message_parts:
                if isinstance(part, tuple) and len(part) == 2:
                    text, tags = part
                    self.chat_history.insert(tk.END, text, tags if tags else None)
                else: 
                    self.chat_history.insert(tk.END, str(part))
            self.chat_history.insert(tk.END, end)
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)

    def _on_closing(self): # Added for menu exit
        print("Closing application...")
        self.master.destroy()

# Mock class for status_bar for testing purposes
class MockStatusBar:
    def config(self, text):
        self.text = text 
    def cget(self, option): 
        if option == "text":
            return getattr(self, "text", "")
        return None

if __name__ == "__main__":
    root = tk.Tk()
    # Pass the default config file path for normal runs
    app = ChatbotGUI(root, config_filepath=CONFIG_FILE) 
    root.mainloop()
