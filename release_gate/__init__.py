"""release-gate: tests, mutation testing, atomic deploy, smoke check, automatic rollback."""
from .deploy import current_release, deploy, rollback
from .mutate import MutationResult, run_mutation
from .pipeline import GateResult, run_pipeline

__all__ = ["run_pipeline", "GateResult", "run_mutation", "MutationResult",
           "deploy", "rollback", "current_release"]
