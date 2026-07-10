class MergeGate:
    @staticmethod
    def decide(
        rule_matched: bool,
        template_applied: bool,
        is_replay_match: bool
    ) -> str:
        """
        Determines the merge gate status:
        - ALLOW: Rule matched, template applied, and Run 1 matches Run 2.
        - BLOCK: Rule matched, template applied, but Run 1 does not match Run 2.
        - REVIEW: No rule matched or no deterministic template is available.
        """
        if not rule_matched or not template_applied:
            return "REVIEW"
        
        if is_replay_match:
            return "ALLOW"
        else:
            return "BLOCK"
