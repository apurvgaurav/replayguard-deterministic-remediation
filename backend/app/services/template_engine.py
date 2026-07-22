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

        try:
            search_pattern = template.get("search_pattern", "")
            replace_pattern = template.get("replace_pattern", "")
            expected_primary_count = template.get("expected_match_count", 1)
            additional_imports = template.get("additional_imports", [])

            # 1. Primary replacement using re.subn
            patched_code, primary_count = re.subn(search_pattern, replace_pattern, code, flags=re.MULTILINE)
            if primary_count != expected_primary_count:
                return None

            # 2. Process follow-up replacements if specified
            follow_ups = template.get("follow_up_replacements", [])
            for f in follow_ups:
                f_search = f.get("search_pattern", "")
                f_replace = f.get("replace_pattern", "")
                f_expected = f.get("expected_match_count", 1)
                patched_code, f_count = re.subn(f_search, f_replace, patched_code, flags=re.MULTILINE)
                if f_count != f_expected:
                    return None

            # If replacement output is unchanged, fail closed
            if patched_code == code:
                return None

            # 3. Add imports if necessary
            for imp in additional_imports:
                if imp not in patched_code:
                    patched_code = f"{imp}\n" + patched_code

            # 4. Postcondition validation
            required_post = template.get("required_postconditions", [])
            for req in required_post:
                if not re.search(req, patched_code, flags=re.MULTILINE):
                    return None

            forbidden_post = template.get("forbidden_postconditions", [])
            for forb in forbidden_post:
                if re.search(forb, patched_code, flags=re.MULTILINE):
                    return None

            return patched_code
        except Exception:
            # Catch malformed template regex/configuration errors and fail closed
            return None
