# Core prompt generation logic
import re
from pathlib import Path

def parse_template(template_path: Path) -> list[str]:
    """
    Reads a template file and parses it to find placeholders.

    Args:
        template_path: The path to the template file.

    Returns:
        A list of unique placeholder names found in the template.
    """
    try:
        content = template_path.read_text()
        placeholders = re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", content)
        return sorted(list(set(placeholders)))
    except FileNotFoundError:
        return []