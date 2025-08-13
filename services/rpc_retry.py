"""
Phase 7.3: Performance Optimization - RPC Retry Logic
Implements retry logic and failover for RPC calls
"""

import logging
import time
from typing import Any, Callable, Optional, List
from functools import wraps
import random

logger = logging.getLogger(__name__)

class RPCRetryManager:
    """
    Manages RPC retries and failover for blockchain calls
    Phase 7 optimization for handling RPC failures
    """
    
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1  # seconds
        self.max_delay = 10  # seconds
        self.jitter = 0.1  # 10% jitter
        
    def with_retry(self, func: Callable) -> Callable:
        """
        Decorator to add retry logic to RPC calls
        Uses exponential backoff with jitter
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < self.max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = min(
                            self.base_delay * (2 ** attempt),
                            self.max_delay
                        )
                        
                        # Add jitter to prevent thundering herd
                        jitter_amount = delay * self.jitter * random.random()
                        delay += jitter_amount
                        
                        logger.debug(
                            f"RPC call failed (attempt {attempt + 1}/{self.max_retries}), "
                            f"retrying in {delay:.2f}s: {e}"
                        )
                        
                        time.sleep(delay)
                    else:
                        logger.warning(
                            f"RPC call failed after {self.max_retries} attempts: {e}"
                        )
            
            # Re-raise the last exception if all retries failed
            if last_exception:
                raise last_exception
                
        return wrapper
    
    def batch_requests(self, requests: List[dict]) -> List[Any]:
        """
        Batch multiple RPC requests for efficiency
        Reduces number of round trips to RPC endpoint
        """
        # This would be implemented with the actual Web3 batch request
        # For now, it's a placeholder for the optimization
        return []
    
    def get_optimal_endpoint(self, endpoints: List[str]) -> Optional[str]:
        """
        Select the optimal RPC endpoint based on latency
        Implements failover between multiple endpoints
        """
        if not endpoints:
            return None
        
        best_endpoint = None
        best_latency = float('inf')
        
        for endpoint in endpoints:
            try:
                # Measure latency with a simple request
                start = time.time()
                # Would make actual test request here
                latency = time.time() - start
                
                if latency < best_latency:
                    best_latency = latency
                    best_endpoint = endpoint
                    
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} failed latency test: {e}")
                continue
        
        return best_endpoint

# Singleton instance
rpc_retry = RPCRetryManager()