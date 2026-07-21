class MergeGate:
    @staticmethod
    def decide(
        rule_matched: bool,
        template_applied: bool,
        is_replay_match: bool,
        evidence_persisted: bool = False
    ) -> str:
        """
        Determines the merge gate status:
        - ALLOW: Rule matched, template applied, Run 1 matches Run 2, and evidence is successfully persisted.
        - BLOCK: Rule matched, template applied, but Run 1 does not match Run 2 (or evidence not persisted).
        - REVIEW: No rule matched or no deterministic template is available.
        """
        if not rule_matched or not template_applied:
            return "REVIEW"
        
        if is_replay_match and evidence_persisted:
            return "ALLOW"
        else:
            return "BLOCK"
