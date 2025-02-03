import os
import sys
from datetime import datetime

from colorama import Fore, Style, init
import tiktoken

# Configure language model
LANGUAGE_MODEL = 'gemini'  # Options: 'gpt' or 'gemini'

# Excluded domains list
EXCLUDE_DOMAIN = [
    "msn.com",
    "reuters.com",
    "nme.com",
    "thestar.co.uk",
    "go.com",
    "dexerto.com",
    "ashahi.com",
    "sky.com"
]

# Category definitions
CATEGORY = {
    'KEntertainment': 11,
    'KFood': 12,
    'KIssue': 13,
    'Uncategorized': 1
}

# Initialize colorama with auto-reset enabled
init(autoreset=True)


def log(message: str) -> None:
    """
    Print a log message with a green prefix and timestamp.

    Args:
        message (str): The message to log.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.GREEN}[LOG]{Style.RESET_ALL} [{current_time}] {message}")


def error(message: str) -> None:
    """
    Print an error message with a red prefix and timestamp.

    Args:
        message (str): The error message to log.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} [{current_time}] {message}")


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in the given text using the tiktoken library.

    Args:
        text (str): The input text to be tokenized.
        model (str): The language model to use for encoding. Defaults to "gpt-4".

    Returns:
        int: The number of tokens in the text.
    """
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)


# Example usage:
# log("This is a standard log message.")
# error("This is an error message.")
# token_count = count_tokens("This is a sample text.", model=LANGUAGE_MODEL)
# log(f"Token count: {token_count}")