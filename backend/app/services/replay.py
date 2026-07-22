import uuid
from typing import Tuple, Optional
from app.services.normalize import normalize_code
from app.services.template_engine import TemplateEngine

class ReplayController:
    def __init__(self):
        self.template_engine = TemplateEngine()

    def run_replays(
        self, 
        rule_id: str, 
        code: str, 
        simulate_non_determinism: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Executes two independent patch generation runs.
        If simulate_non_determinism is True, Run 2 will include a non-deterministic token/comment
        to trigger a byte-level mismatch.
        """
        normalized_input = normalize_code(code)
        
        # Run 1
        patch_1 = self.template_engine.apply_remediation(rule_id, normalized_input)
        if patch_1:
            patch_1 = normalize_code(patch_1)

        # Run 2
        patch_2 = self.template_engine.apply_remediation(rule_id, normalized_input)
        if patch_2:
            patch_2 = normalize_code(patch_2)
            if simulate_non_determinism:
                # Inject a dynamic/random identifier as a comment to simulate LLM/non-deterministic noise
                random_token = uuid.uuid4().hex[:8]
                patch_2 += f"\n\n# ReplayGuard Non-Deterministic Seed: {random_token}"
                patch_2 = normalize_code(patch_2)

        return patch_1, patch_2
