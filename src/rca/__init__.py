"""Frozen FlashTicket RCA core.

This package is the reusable Task F implementation boundary.  It contains no
dataset roster, ground truth, development selector, or final-campaign logic.
"""

from .contracts import FrozenReleaseConfig, FrozenConfigError, load_frozen_config
from .adapters import AdapterQualificationError, QualifiedTelemetryAdapter
from .observation import C1Observation, C5Observation, ObservationError
from .packet import PacketValidationError, validate_packet
from .pipeline import FrozenRcaPipeline
from .release import ReleaseVerificationError, verify_frozen_release

__all__ = [
    "C1Observation",
    "C5Observation",
    "AdapterQualificationError",
    "FrozenConfigError",
    "FrozenReleaseConfig",
    "FrozenRcaPipeline",
    "ObservationError",
    "PacketValidationError",
    "QualifiedTelemetryAdapter",
    "ReleaseVerificationError",
    "load_frozen_config",
    "validate_packet",
    "verify_frozen_release",
]
