from .models import ApprovalDecision, ApprovalRecord, ApprovalRequest, ApprovalStatus
from .policy import ApprovalPolicyChecker, ApprovalPolicyInput

__all__ = [
    "ApprovalCliInput",
    "ApprovalDecision",
    "ApprovalPolicyChecker",
    "ApprovalPolicyInput",
    "ApprovalRecord",
    "ApprovalRequest",
    "ApprovalService",
    "ApprovalStatus",
    "ApprovalStore",
    "DEFAULT_APPROVAL_TTL_MINUTES",
    "future_expiry_iso",
    "parse_scope",
]


def __getattr__(name: str):
    if name == "ApprovalStore":
        from .store import ApprovalStore

        return ApprovalStore
    if name in {"ApprovalCliInput", "ApprovalService", "DEFAULT_APPROVAL_TTL_MINUTES", "future_expiry_iso", "parse_scope"}:
        from . import service as _service

        return getattr(_service, name)
    raise AttributeError(name)
