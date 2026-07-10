import re
import json
from pathlib import Path
from typing import Optional, Dict, Any

class RuleEngine:
    def __init__(self):
        self.rules_path = Path(__file__).parent.parent / "demo_data" / "rules.json"
        self.rules = []
        self._load_rules()

    def _load_rules(self):
        try:
            with open(self.rules_path, "r") as f:
                self.rules = json.load(f)
        except Exception as e:
            print(f"Error loading rules.json: {e}")
            self.rules = []

    def scan(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Scans code using regex patterns from the rules database.
        Returns the first matched rule, or None if safe.
        """
        for rule in self.rules:
            pattern = rule.get("pattern", "")
            if pattern:
                # Use multiline and dotall flag for multi-line code blocks
                if re.search(pattern, code, re.MULTILINE | re.DOTALL):
                    return rule
        return None
