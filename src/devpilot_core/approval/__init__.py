from .models import ApprovalDecision, ApprovalRecord, ApprovalRequest, ApprovalStatus

__all__ = [
    "ApprovalBindingOptions",
    "ApprovalBindingRequest",
    "ApprovalCliInput",
    "ApprovalDecision",
    "ApprovalPolicyChecker",
    "ApprovalPolicyInput",
    "ApprovalRecord",
    "ApprovalRequest",
    "ApprovalService",
    "StrongApprovalBindingValidator",
    "compute_subject_hash",
    "ApprovalStatus",
    "ApprovalStore",
    "DEFAULT_APPROVAL_TTL_MINUTES",
    "future_expiry_iso",
    "parse_scope",
]


def __getattr__(name: str):
    if name in {"ApprovalBindingOptions", "ApprovalBindingRequest", "StrongApprovalBindingValidator", "compute_subject_hash"}:
        from . import binding as _binding

        return getattr(_binding, name)
    if name == "ApprovalStore":
        from .store import ApprovalStore

        return ApprovalStore
    if name in {"ApprovalPolicyChecker", "ApprovalPolicyInput"}:
        from . import policy as _policy

        return getattr(_policy, name)
    if name in {"ApprovalCliInput", "ApprovalService", "DEFAULT_APPROVAL_TTL_MINUTES", "future_expiry_iso", "parse_scope"}:
        from . import service as _service

        return getattr(_service, name)
    raise AttributeError(name)
