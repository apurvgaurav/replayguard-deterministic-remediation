class MergeGate:
    @staticmethod
    def decide(
        rule_matched: bool,
        template_applied: bool,
        is_replay_match: bool,
        evidence_persisted: bool = False,
        template_postconditions_passed: bool = False
    ) -> str:
        """
        Determines the merge gate status:
        - REVIEW: No rule matched or no deterministic template is available.
        - BLOCK: Rule matched, template applied, but any of the following failed:
                 - template_postconditions_passed is False
                 - replay outputs mismatch (is_replay_match is False)
                 - evidence was not persisted (evidence_persisted is False)
        - ALLOW: All security gates passed.
        """
        if not rule_matched or not template_applied:
            return "REVIEW"
        if not template_postconditions_passed:
            return "BLOCK"
        if not is_replay_match:
            return "BLOCK"
        if not evidence_persisted:
            return "BLOCK"
        return "ALLOW"
