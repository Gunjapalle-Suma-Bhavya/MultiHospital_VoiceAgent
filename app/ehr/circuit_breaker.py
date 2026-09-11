"""
EHR Integration Circuit Breaker & Resilience Controller (Section 27).

Protects against cascading failures and network partitions during external hospital EHR outages.
Implements the 3-state Circuit Breaker pattern:
- CLOSED: Normal operation, all external calls pass through.
- OPEN: Outage detected, fail-fast prevents hammering downstream EHR, requests routed to asynchronous retry queue.
- HALF_OPEN: Probe requests verify if the external EHR has recovered.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import threading


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class EHRCircuitBreaker:
    """
    Thread-safe circuit breaker controlling calls to external healthcare systems.
    """

    def __init__(
        self,
        name: str = "EHR_PRIMARY",
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 5.0,
        success_threshold_half_open: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self.success_threshold = success_threshold_half_open

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_state_change = datetime.now(timezone.utc)
        self._last_failure_reason: Optional[str] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            now = datetime.now(timezone.utc)
            if self._state == CircuitState.OPEN:
                if now - self._last_state_change >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._consecutive_successes = 0
                    self._last_state_change = now
            return self._state

    def can_execute(self) -> bool:
        """Determines if a request should be dispatched to the external system."""
        current_state = self.state
        return current_state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self):
        """Records a successful response from external EHR."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._consecutive_successes += 1
                if self._consecutive_successes >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._consecutive_failures = 0
                    self._consecutive_successes = 0
                    self._last_state_change = datetime.now(timezone.utc)
            elif self._state == CircuitState.CLOSED:
                self._consecutive_failures = 0

    def record_failure(self, error_reason: str):
        """Records a network or API failure from external EHR."""
        with self._lock:
            self._last_failure_reason = error_reason
            self._consecutive_failures += 1
            if self._state == CircuitState.HALF_OPEN:
                # Immediate trip back to OPEN
                self._state = CircuitState.OPEN
                self._last_state_change = datetime.now(timezone.utc)
            elif self._state == CircuitState.CLOSED:
                if self._consecutive_failures >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._last_state_change = datetime.now(timezone.utc)

    def reset(self):
        """Manually forces the circuit breaker back to CLOSED state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._consecutive_successes = 0
            self._last_state_change = datetime.now(timezone.utc)
            self._last_failure_reason = None

    def get_status(self) -> Dict[str, Any]:
        """Returns live diagnostics of the circuit breaker."""
        current_state = self.state
        return {
            "name": self.name,
            "state": current_state.value,
            "can_execute": self.can_execute(),
            "consecutive_failures": self._consecutive_failures,
            "failure_threshold": self.failure_threshold,
            "consecutive_successes": self._consecutive_successes,
            "last_failure_reason": self._last_failure_reason,
            "last_state_change": self._last_state_change.isoformat(),
            "recovery_timeout_seconds": self.recovery_timeout.total_seconds()
        }


# Global primary instance for application-wide EHR calls
default_ehr_circuit_breaker = EHRCircuitBreaker()
