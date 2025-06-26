"""
🚦 Google Gemini API Quota Manager
Intelligent quota management and circuit breaker for API rate limiting

Features:
- Circuit breaker pattern for 429 errors
- Exponential backoff with jitter
- Quota usage tracking
- Graceful degradation
- Health monitoring
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import random
import json

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Blocking requests due to failures
    HALF_OPEN = "half_open" # Testing if service is recovered

class QuotaErrorType(Enum):
    """Types of quota/rate limit errors"""
    RATE_LIMIT = "rate_limit"           # 429 Too Many Requests
    QUOTA_EXCEEDED = "quota_exceeded"   # Daily/monthly quota exceeded
    RESOURCE_EXHAUSTED = "resource_exhausted"  # Google's resource exhausted
    UNKNOWN = "unknown"

@dataclass
class QuotaMetrics:
    """Quota usage metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    quota_errors: int = 0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    current_backoff_delay: float = 1.0
    circuit_state: CircuitState = CircuitState.CLOSED
    circuit_open_time: Optional[datetime] = None
    error_history: list = field(default_factory=list)

class QuotaManager:
    """Google Gemini API Quota Manager with Circuit Breaker"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 300,  # 5 minutes
                 max_backoff_delay: int = 3600,  # 1 hour
                 base_delay: float = 1.0,
                 backoff_multiplier: float = 2.0):
        
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.max_backoff_delay = max_backoff_delay
        self.base_delay = base_delay
        self.backoff_multiplier = backoff_multiplier
        
        self.metrics = QuotaMetrics()
        self.quota_reset_time: Optional[datetime] = None
        self.daily_quota_used = 0
        self.daily_quota_limit = 1000  # Conservative estimate
        
        # Error pattern detection
        self.error_patterns = {
            "429": QuotaErrorType.RATE_LIMIT,
            "Resource has been exhausted": QuotaErrorType.RESOURCE_EXHAUSTED,
            "quota": QuotaErrorType.QUOTA_EXCEEDED,
            "rate limit": QuotaErrorType.RATE_LIMIT
        }
        
        logger.info(f"🚦 Quota Manager initialized - Failure threshold: {failure_threshold}, Recovery timeout: {recovery_timeout}s")
    
    async def execute_with_quota_management(self, 
                                          operation: Callable,
                                          operation_name: str = "API_CALL",
                                          *args, **kwargs) -> Any:
        """
        Execute an operation with quota management and circuit breaker
        
        Args:
            operation: The async function to execute
            operation_name: Name for logging purposes
            *args, **kwargs: Arguments to pass to the operation
            
        Returns:
            Result of the operation
            
        Raises:
            QuotaExhaustedException: When quota is exhausted and circuit is open
            Exception: Original exception if not quota-related
        """
        
        # Check circuit breaker state
        if not await self._can_execute():
            raise QuotaExhaustedException(
                f"Circuit breaker is OPEN. Service unavailable until {self.quota_reset_time or 'unknown'}"
            )
        
        # Apply current backoff delay
        if self.metrics.current_backoff_delay > self.base_delay:
            jitter = random.uniform(0.1, 0.3) * self.metrics.current_backoff_delay
            delay = self.metrics.current_backoff_delay + jitter
            logger.info(f"⏳ Applying backoff delay: {delay:.2f}s for {operation_name}")
            await asyncio.sleep(delay)
        
        start_time = time.time()
        
        try:
            # Execute the operation
            self.metrics.total_requests += 1
            result = await operation(*args, **kwargs)
            
            # Success - reset failure metrics
            await self._record_success()
            
            execution_time = time.time() - start_time
            logger.debug(f"✅ {operation_name} completed successfully in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_type = self._classify_error(str(e))
            
            await self._record_failure(e, error_type, operation_name)
            
            logger.error(f"❌ {operation_name} failed after {execution_time:.2f}s: {e}")
            
            # Re-raise the original exception
            raise
    
    async def _can_execute(self) -> bool:
        """Check if we can execute a request based on circuit breaker state"""
        
        if self.metrics.circuit_state == CircuitState.CLOSED:
            return True
        
        elif self.metrics.circuit_state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self.metrics.circuit_open_time and 
                datetime.now() - self.metrics.circuit_open_time > timedelta(seconds=self.recovery_timeout)):
                
                logger.info("🔄 Circuit breaker transitioning to HALF_OPEN for testing")
                self.metrics.circuit_state = CircuitState.HALF_OPEN
                return True
            
            return False
        
        elif self.metrics.circuit_state == CircuitState.HALF_OPEN:
            # In half-open state, allow limited testing
            return True
        
        return False
    
    async def _record_success(self):
        """Record a successful operation"""
        self.metrics.successful_requests += 1
        self.metrics.last_success_time = datetime.now()
        self.metrics.consecutive_failures = 0
        
        # Reset backoff delay on success
        self.metrics.current_backoff_delay = self.base_delay
        
        # Close circuit if it was open or half-open
        if self.metrics.circuit_state != CircuitState.CLOSED:
            logger.info("✅ Circuit breaker closing - Service recovered")
            self.metrics.circuit_state = CircuitState.CLOSED
            self.metrics.circuit_open_time = None
    
    async def _record_failure(self, error: Exception, error_type: QuotaErrorType, operation_name: str):
        """Record a failed operation and update circuit breaker state"""
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = datetime.now()
        self.metrics.consecutive_failures += 1
        
        # Add to error history (keep last 100 errors)
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "type": error_type.value,
            "operation": operation_name
        }
        self.metrics.error_history.append(error_record)
        if len(self.metrics.error_history) > 100:
            self.metrics.error_history.pop(0)
        
        # Handle quota-specific errors
        if error_type in [QuotaErrorType.RATE_LIMIT, QuotaErrorType.RESOURCE_EXHAUSTED, QuotaErrorType.QUOTA_EXCEEDED]:
            self.metrics.quota_errors += 1
            await self._handle_quota_error(error_type)
        
        # Check if we should open the circuit breaker
        if (self.metrics.consecutive_failures >= self.failure_threshold and 
            self.metrics.circuit_state == CircuitState.CLOSED):
            
            await self._open_circuit()
        
        # Update backoff delay
        self.metrics.current_backoff_delay = min(
            self.metrics.current_backoff_delay * self.backoff_multiplier,
            self.max_backoff_delay
        )
    
    async def _handle_quota_error(self, error_type: QuotaErrorType):
        """Handle specific quota error types"""
        
        if error_type == QuotaErrorType.RATE_LIMIT:
            # Short-term rate limiting - increase backoff
            self.metrics.current_backoff_delay = min(
                self.metrics.current_backoff_delay * 1.5,
                300  # Max 5 minutes for rate limiting
            )
            logger.warning(f"⚠️ Rate limit hit - increasing backoff to {self.metrics.current_backoff_delay:.2f}s")
        
        elif error_type == QuotaErrorType.RESOURCE_EXHAUSTED:
            # Google's resources exhausted - longer backoff
            self.metrics.current_backoff_delay = min(
                self.metrics.current_backoff_delay * 3.0,
                1800  # Max 30 minutes for resource exhaustion
            )
            logger.warning(f"⚠️ Resources exhausted - increasing backoff to {self.metrics.current_backoff_delay:.2f}s")
            
            # Estimate quota reset time (usually resets hourly or daily)
            self.quota_reset_time = datetime.now() + timedelta(hours=1)
        
        elif error_type == QuotaErrorType.QUOTA_EXCEEDED:
            # Daily/monthly quota exceeded - long backoff
            self.metrics.current_backoff_delay = self.max_backoff_delay
            logger.error(f"❌ Quota exceeded - setting maximum backoff: {self.max_backoff_delay}s")
            
            # Estimate quota reset time (usually daily)
            self.quota_reset_time = datetime.now() + timedelta(days=1)
    
    async def _open_circuit(self):
        """Open the circuit breaker"""
        logger.error(f"🚨 Circuit breaker OPENING - {self.metrics.consecutive_failures} consecutive failures")
        self.metrics.circuit_state = CircuitState.OPEN
        self.metrics.circuit_open_time = datetime.now()
        
        # Set quota reset time if not already set
        if not self.quota_reset_time:
            self.quota_reset_time = datetime.now() + timedelta(seconds=self.recovery_timeout)
    
    def _classify_error(self, error_message: str) -> QuotaErrorType:
        """Classify error type based on error message"""
        error_lower = error_message.lower()
        
        for pattern, error_type in self.error_patterns.items():
            if pattern.lower() in error_lower:
                return error_type
        
        return QuotaErrorType.UNKNOWN
    
    def get_status(self) -> Dict[str, Any]:
        """Get current quota manager status"""
        return {
            "circuit_state": self.metrics.circuit_state.value,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "quota_errors": self.metrics.quota_errors,
            "consecutive_failures": self.metrics.consecutive_failures,
            "current_backoff_delay": self.metrics.current_backoff_delay,
            "success_rate": (
                self.metrics.successful_requests / max(self.metrics.total_requests, 1) * 100
            ),
            "quota_reset_time": self.quota_reset_time.isoformat() if self.quota_reset_time else None,
            "last_success": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
            "last_failure": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
            "recent_errors": self.metrics.error_history[-5:] if self.metrics.error_history else []
        }
    
    def reset_circuit(self):
        """Manually reset the circuit breaker (admin function)"""
        logger.info("🔄 Manually resetting circuit breaker")
        self.metrics.circuit_state = CircuitState.CLOSED
        self.metrics.circuit_open_time = None
        self.metrics.consecutive_failures = 0
        self.metrics.current_backoff_delay = self.base_delay
        self.quota_reset_time = None

class QuotaExhaustedException(Exception):
    """Exception raised when quota is exhausted and circuit breaker is open"""
    pass

# Global quota manager instance
quota_manager = QuotaManager()