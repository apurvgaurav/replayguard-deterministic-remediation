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
        simulate_non_determinism: bool = False,
        status: Optional[dict] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Executes two deterministic remediation runs.
        If simulate_non_determinism is True, Run 2 will include a non-deterministic token/comment
        to trigger a byte-level mismatch.
        """
        normalized_input = normalize_code(code)

        run_1_status = {}
        run_2_status = {}

        # Run 1
        patch_1 = self.template_engine.apply_remediation(rule_id, normalized_input, run_1_status)
        if patch_1:
            patch_1 = normalize_code(patch_1)

        # Run 2
        patch_2 = self.template_engine.apply_remediation(rule_id, normalized_input, run_2_status)
        if patch_2:
            patch_2 = normalize_code(patch_2)
            if simulate_non_determinism:
                # Inject a dynamic/random identifier as a comment to simulate LLM/non-deterministic noise
                random_token = uuid.uuid4().hex[:8]
                patch_2 += f"\n\n# ReplayGuard Controlled Fault Injection: {random_token}"
                patch_2 = normalize_code(patch_2)

        if status is not None:
            p1_tid = run_1_status.get("template_id")
            p2_tid = run_2_status.get("template_id")

            p1_passed = run_1_status.get("template_postconditions_passed") is True
            p2_passed = run_2_status.get("template_postconditions_passed") is True

            p1_ver = run_1_status.get("template_version")
            p2_ver = run_2_status.get("template_version")
            p1_hash = run_1_status.get("template_hash")
            p2_hash = run_2_status.get("template_hash")

            if p1_tid is None and p2_tid is None:
                status["template_id"] = None
                status["template_version"] = None
                status["template_hash"] = None
                status["template_postconditions_passed"] = None
            else:
                is_valid = (
                    patch_1 is not None and
                    patch_2 is not None and
                    p1_passed and
                    p2_passed and
                    p1_tid is not None and
                    p1_tid == p2_tid and
                    p1_ver is not None and
                    p1_ver == p2_ver and
                    p1_hash is not None and
                    p1_hash == p2_hash
                )

                status["template_id"] = p1_tid if is_valid else None
                status["template_version"] = p1_ver if is_valid else None
                status["template_hash"] = p1_hash if is_valid else None
                status["template_postconditions_passed"] = True if is_valid else False

        return patch_1, patch_2
