# Helper functions
import json
from pathlib import Path

def save_as_json(data: dict, file_path: Path):
    """
    Saves a dictionary to a file in JSON format.

    Args:
        data: The dictionary to save.
        file_path: The path to the output file.
    """
    with file_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)