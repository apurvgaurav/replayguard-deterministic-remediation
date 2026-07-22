import re
import json
import hashlib
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
    def get_template_for_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        for t in self.templates:
            if t.get("rule_id") == rule_id:
                return t
        return None

    def compute_template_hash(self, template: Dict[str, Any]) -> str:
        canonical_json = json.dumps(template, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def apply_remediation(self, rule_id: str, code: str, status: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Applies a deterministic template replacement to patch the code.
        Prepend imports if they are not already in the file.
        """
        template = self.get_template_for_rule(rule_id)
        if not template:
            return None

        if status is not None:
            status["template_id"] = template.get("id")
            status["template_version"] = template.get("version")
            status["template_hash"] = self.compute_template_hash(template)
            status["template_postconditions_passed"] = False  # Default to False if we fail early

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

            if status is not None:
                status["template_postconditions_passed"] = True

            return patched_code
        except Exception:
            # Catch malformed template regex/configuration errors and fail closed
            if status is not None:
                status["template_postconditions_passed"] = False
            return None
