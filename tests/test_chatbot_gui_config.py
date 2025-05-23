import unittest
import os
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to allow importing chatbot_gui
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatbot_gui import ChatbotGUI, MockStatusBar # Assuming MockStatusBar is in chatbot_gui for testing

class TestConfigManagement(unittest.TestCase):

    def setUp(self):
        self.test_config_filename = "test_chatbot_config.json"
        # Ensure no pre-existing test config file from a previous failed run
        if os.path.exists(self.test_config_filename):
            os.remove(self.test_config_filename)
        
        # Mock GUI elements that might be called during config load/save
        # if ChatbotGUI is instantiated with master=None, it should use MockStatusBar
        # We also need to patch messagebox if it's called directly by _load_config or _save_config
        self.patcher_messagebox = patch('chatbot_gui.messagebox')
        self.mock_messagebox = self.patcher_messagebox.start()

        # Minimal master mock if needed for basic Tkinter calls, but prefer master=None
        self.mock_master = MagicMock() 
        # Simulate winfo_exists returning True for certain messagebox calls in _load_config
        self.mock_master.winfo_exists.return_value = True 


    def tearDown(self):
        if os.path.exists(self.test_config_filename):
            os.remove(self.test_config_filename)
        self.patcher_messagebox.stop()

    def _get_default_config(self):
        return {
            "base_url": "http://127.0.0.1:1234/v1",
            "model_name": "qwen2.5-7b-instruct-1m",
            "weather_api_key": ""
        }

    def test_load_no_config_file(self):
        """Test loading config when no file exists."""
        # Pass master=None for headless operation, relying on MockStatusBar if status_bar is used.
        # Pass run_gui_setup=False to prevent full UI initialization.
        # However, _load_config is called in __init__. We need to control config_filepath.
        gui = ChatbotGUI(master=self.mock_master, config_filepath=self.test_config_filename, run_gui_setup=False)
        
        defaults = self._get_default_config()
        self.assertEqual(gui.config, defaults)
        self.assertTrue(os.path.exists(self.test_config_filename))
        with open(self.test_config_filename, 'r') as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config, defaults)
        # Check if messagebox was called (it should be, by _save_config via _load_config)
        # self.mock_messagebox.showwarning.assert_not_called() # No warning if creating new
        # self.mock_messagebox.showerror.assert_not_called() # No error if creating new

    def test_load_existing_valid_config(self):
        """Test loading an existing and valid config file."""
        custom_settings = {
            "base_url": "http://localhost:8080/v1",
            "model_name": "custom_model_test",
            "weather_api_key": "test_key_123"
        }
        with open(self.test_config_filename, 'w') as f:
            json.dump(custom_settings, f)

        gui = ChatbotGUI(master=self.mock_master, config_filepath=self.test_config_filename, run_gui_setup=False)
        self.assertEqual(gui.config, custom_settings)
        self.mock_messagebox.showwarning.assert_not_called()
        self.mock_messagebox.showerror.assert_not_called()


    def test_load_corrupted_json_config(self):
        """Test loading a corrupted JSON config file."""
        with open(self.test_config_filename, 'w') as f:
            f.write("{'invalid_json': ") # Corrupted JSON

        gui = ChatbotGUI(master=self.mock_master, config_filepath=self.test_config_filename, run_gui_setup=False)
        
        defaults = self._get_default_config()
        self.assertEqual(gui.config, defaults) # Should load defaults
        # Check if the corrupted file was overwritten with defaults
        with open(self.test_config_filename, 'r') as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config, defaults)
        self.mock_messagebox.showwarning.assert_called_once() # Should warn about corruption


    def test_load_missing_keys_config(self):
        """Test loading a config file with missing keys."""
        partial_settings = {
            "base_url": "http://partial_url:5000/v1",
            # model_name is missing
            # weather_api_key is missing
        }
        with open(self.test_config_filename, 'w') as f:
            json.dump(partial_settings, f)

        gui = ChatbotGUI(master=self.mock_master, config_filepath=self.test_config_filename, run_gui_setup=False)
        
        expected_config = self._get_default_config()
        expected_config.update(partial_settings) # Update defaults with loaded partial settings

        self.assertEqual(gui.config["base_url"], partial_settings["base_url"])
        self.assertEqual(gui.config["model_name"], self._get_default_config()["model_name"])
        self.assertEqual(gui.config["weather_api_key"], self._get_default_config()["weather_api_key"])
        self.mock_messagebox.showwarning.assert_not_called() # No warning if just missing keys, defaults are used silently


    def test_save_basic_config(self):
        """Test saving a basic configuration."""
        gui = ChatbotGUI(master=self.mock_master, config_filepath=self.test_config_filename, run_gui_setup=False)
        
        test_settings = {
            "base_url": "http://saved_url:1234/v1",
            "model_name": "saved_model",
            "weather_api_key": "saved_key_xyz"
        }
        gui.config = test_settings.copy() # Set the config to be saved
        gui._save_config()

        self.assertTrue(os.path.exists(self.test_config_filename))
        with open(self.test_config_filename, 'r') as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config, test_settings)
        # self.mock_messagebox.showerror.assert_not_called() # No error if saving works

    def test_load_config_handles_none_values_from_file(self):
        """Test loading config where some keys might have null/None values from file."""
        # This can happen if a config file was manually edited to have "key": null
        settings_with_null = {
            "base_url": "http://testurl.com/v1",
            "model_name": None, # Explicitly None
            "weather_api_key": "some_key"
        }
        with open(self.test_config_filename, 'w') as f:
            json.dump(settings_with_null, f)

        gui = ChatbotGUI(master=self.mock_master, config_filepath=self.test_config_filename, run_gui_setup=False)
        
        defaults = self._get_default_config()
        self.assertEqual(gui.config["base_url"], "http://testurl.com/v1")
        self.assertEqual(gui.config["model_name"], defaults["model_name"]) # Should revert to default for None
        self.assertEqual(gui.config["weather_api_key"], "some_key")


if __name__ == '__main__':
    unittest.main()
