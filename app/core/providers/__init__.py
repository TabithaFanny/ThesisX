"""ThesisX Provider configuration system — detection, health checks, profiles.

Local CLI providers, remote API providers, and Agent Team providers are
discovered via read-only probing (no API calls unless explicitly opted-in).
"""

from .models import (  # noqa: F401
    AgentTeamProvider,
    LocalCLIProvider,
    ProviderHealthStatus,
    ProviderKind,
    RemoteAPIProvider,
    RuntimeProfile,
)
from .detector import (  # noqa: F401
    discover_local_clis,
    detect_remote_api_config,
    detect_agent_team_paths,
    generate_provider_health_report,
)

__all__ = [
    "ProviderKind",
    "LocalCLIProvider",
    "RemoteAPIProvider",
    "AgentTeamProvider",
    "RuntimeProfile",
    "ProviderHealthStatus",
    "discover_local_clis",
    "detect_remote_api_config",
    "detect_agent_team_paths",
    "generate_provider_health_report",
]
