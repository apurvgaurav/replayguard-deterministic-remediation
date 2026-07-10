import re
import json
from pathlib import Path
from typing import Optional, Dict, Any

class TemplateEngine:
    def __init__(self):
        self.templates_path = Path(__file__).parent.parent / "demo_data" / "templates.json"
        self.templates = []
        self._load_templates()

    def _load_templates(self):
        try:
            with open(self.templates_path, "r") as f:
                self.templates = json.load(f)
        except Exception as e:
            print(f"Error loading templates.json: {e}")
            self.templates = []

    def apply_remediation(self, rule_id: str, code: str) -> Optional[str]:
        """
        Applies a deterministic template replacement to patch the code.
        Prepend imports if they are not already in the file.
        """
        template = None
        for t in self.templates:
            if t.get("rule_id") == rule_id:
                template = t
                break
        
        if not template:
            return None

        search_pattern = template.get("search_pattern", "")
        replace_pattern = template.get("replace_pattern", "")
        additional_imports = template.get("additional_imports", [])

        # Perform replacement with MULTILINE flag to support ^ matching line start
        patched_code = re.sub(search_pattern, replace_pattern, code, flags=re.MULTILINE)

        if patched_code == code:
            # If search pattern failed to match exactly, fall back to a simpler search-and-replace
            # or return the code as-is for the comparator to handle.
            pass

        # Add imports if necessary
        for imp in additional_imports:
            if imp not in patched_code:
                patched_code = f"{imp}\n" + patched_code

        return patched_code
