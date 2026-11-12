class SemanticQualityError(Exception):
    """Raised when generated pillar narrative fails deterministic Tier-1 quality gates."""
    def __init__(self, feedback: str, failed_text: str = ""):
        super().__init__(feedback)
        self.feedback = feedback
        self.failed_text = failed_text
