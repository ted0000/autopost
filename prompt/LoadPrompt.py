import os

from config.config import *

class LoadPrompt():
    def __init__(self, filename):
        self.filename = filename

    def load(self):
        try:
            root = os.path.dirname(__file__)
            prompt_path = os.path.join(root, self.filename)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ERROR(f"File '{self.filename}' not found in {root}.")
        except PermissionError:
            return ERROR(f"Permission denied for file '{self.filename}'.")
        except Exception as e:
            return ERROR(f"An unexpected error occurred - {e}")