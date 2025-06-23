"""
Stability Tracker Utility
Tracks API stability metrics and retry patterns
"""

import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AttemptRecord:
    """Record of a single attempt"""
    success: bool
    attempt_number: int
    timestamp: datetime = field(default_factory=datetime.now)


class StabilityTracker:
    """
    Tracks stability metrics for API operations
    Used by BaseTest for retry logic analysis
    """

    def __init__(self, operation_name: str = "unknown"):
        self.operation_name = operation_name
        self.attempts: List[AttemptRecord] = []
        self.start_time = time.time()

    def record_attempt(self, success: bool, attempt_number: int) -> None:
        """Record the result of an attempt"""
        record = AttemptRecord(
            success=success,
            attempt_number=attempt_number
        )
        self.attempts.append(record)

    def get_summary(self) -> str:
        """Get a brief summary of stability metrics"""
        if not self.attempts:
            return "No attempts recorded"

        total_attempts = len(self.attempts)
        successful_attempts = sum(1 for attempt in self.attempts if attempt.success)
        success_rate = (successful_attempts / total_attempts) * 100

        return f"{success_rate:.1f}% success rate ({successful_attempts}/{total_attempts} attempts)"

    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed stability metrics"""
        if not self.attempts:
            return {"error": "No attempts recorded"}

        total_attempts = len(self.attempts)
        successful_attempts = sum(1 for attempt in self.attempts if attempt.success)

        # Calculate retry statistics
        total_retries = sum(attempt.attempt_number for attempt in self.attempts)
        average_retries = total_retries / total_attempts if total_attempts > 0 else 0

        # First-try success rate
        first_try_successes = sum(1 for attempt in self.attempts
                                  if attempt.success and attempt.attempt_number == 0)
        first_try_success_rate = (first_try_successes / total_attempts) * 100

        # Duration
        duration = time.time() - self.start_time

        return {
            "operation_name": self.operation_name,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": (successful_attempts / total_attempts) * 100,
            "average_retries": average_retries,
            "first_try_success_rate": first_try_success_rate,
            "duration_seconds": round(duration, 2)
        }

    def reset(self) -> None:
        """Reset all tracking data"""
        self.attempts.clear()
        self.start_time = time.time()

    def is_stable(self, threshold: float = 90.0) -> bool:
        """Check if the operation is considered stable"""
        metrics = self.get_metrics()
        if "error" in metrics:
            return False
        return metrics["success_rate"] >= threshold