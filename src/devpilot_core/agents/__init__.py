"""Local/mock DevPilot agent runtime."""

from .base import ModelAwareAgent
from .capability_inventory import (
    AGENT_CAPABILITY_INVENTORY_COMMAND,
    AGENT_CAPABILITY_INVENTORY_CONTRACT,
    AGENT_CAPABILITY_INVENTORY_SCHEMA_ID,
    AGENT_PROMOTION_CRITERIA_CONTRACT,
    AGENT_PROMOTION_CRITERIA_SCHEMA_ID,
    AgentCapabilityInventoryBuilder,
    AgentCapabilityInventoryOptions,
)
from .code_review_agent import CodeReviewAgent
from .patch_review_agent import PatchReviewAgent
from .safe_refactor_agent import SafeRefactorAgent
from .test_planner_agent import TestPlannerAgent
from .models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from .memory import (
    AGENT_MEMORY_COMMAND,
    AGENT_MEMORY_CONTRACT,
    AGENT_MEMORY_SCHEMA_ID,
    AgentMemoryModelManager,
    AgentMemoryModelOptions,
)

from .tool_calls import (
    AGENT_TOOL_CALL_COMMAND,
    AGENT_TOOL_CALL_CONTRACT,
    AGENT_TOOL_CALL_SCHEMA_ID,
    AgentToolCallingContractManager,
    AgentToolCallingContractOptions,
)
from .repo_analysis_agent import RepoAnalysisAgent
from .release_agent import ReleaseAgent
from .architecture_agent import ArchitectureAgent
from .requirements_agent import RequirementsAgent
from .runtime import AgentRuntime, AgentRuntimeConfig
from .role_bindings import AgentRoleBindingCatalog, AgentRoleDescriptor, StepAgentBinding
from .rag_context import (
    INSUFFICIENT_EVIDENCE,
    RAG_AGENT_CONTEXT_COMMAND,
    RAG_AGENT_CONTEXT_CONTRACT,
    RAG_AGENT_CONTEXT_SCHEMA_ID,
    RagAgentContextOptions,
    RagAwareAgentContextBuilder,
)
from .session import AgentSession, AgentSessionEvent, AgentSessionInspectOptions, AgentSessionStore, inspect_agent_session
from .security_agent import SecurityAgent

__all__ = [
    "AGENT_TOOL_CALL_COMMAND",
    "AGENT_TOOL_CALL_CONTRACT",
    "AGENT_TOOL_CALL_SCHEMA_ID",
    "AgentToolCallingContractManager",
    "AgentToolCallingContractOptions",
    "AGENT_MEMORY_COMMAND",
    "AGENT_MEMORY_CONTRACT",
    "AGENT_MEMORY_SCHEMA_ID",
    "AgentMemoryModelManager",
    "AgentMemoryModelOptions",
    "AGENT_CAPABILITY_INVENTORY_COMMAND",
    "AGENT_CAPABILITY_INVENTORY_CONTRACT",
    "AGENT_CAPABILITY_INVENTORY_SCHEMA_ID",
    "AGENT_PROMOTION_CRITERIA_CONTRACT",
    "AGENT_PROMOTION_CRITERIA_SCHEMA_ID",
    "AgentCapabilityInventoryBuilder",
    "AgentCapabilityInventoryOptions",
    "AgentMessage",
    "AgentModelCall",
    "AgentRunResult",
    "AgentRuntime",
    "INSUFFICIENT_EVIDENCE",
    "RAG_AGENT_CONTEXT_COMMAND",
    "RAG_AGENT_CONTEXT_CONTRACT",
    "RAG_AGENT_CONTEXT_SCHEMA_ID",
    "RagAgentContextOptions",
    "RagAwareAgentContextBuilder",
    "AgentRuntimeConfig",
    "AgentRoleBindingCatalog",
    "AgentRoleDescriptor",
    "StepAgentBinding",
    "AgentSession",
    "AgentSessionEvent",
    "AgentSessionInspectOptions",
    "AgentSessionStore",
    "inspect_agent_session",
    "RequirementsAgent",
    "ArchitectureAgent",
    "SecurityAgent",
    "ReleaseAgent",
    "RepoAnalysisAgent",
    "CodeReviewAgent",
    "PatchReviewAgent",
    "SafeRefactorAgent",
    "TestPlannerAgent",
    "AgentSuggestion",
    "AgentToolCall",
    "ModelAwareAgent",
]

# DEVPL-GSDLC-07-D bounded execution successor contracts.
from .execution_policy import AgentExecutionPolicy, ToolIntent, ToolExecutionDecision
