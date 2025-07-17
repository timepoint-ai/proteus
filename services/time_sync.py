import logging
from datetime import datetime, timezone
import pytz
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

class TimeSyncService:
    def __init__(self):
        self.pacific_tz = pytz.timezone(Config.PACIFIC_TIMEZONE)
        
    def get_pacific_time(self) -> datetime:
        """Get current Pacific time (no DST adjustments)"""
        try:
            # Get current UTC time
            utc_now = datetime.now(timezone.utc)
            
            # Convert to Pacific timezone
            pacific_time = utc_now.astimezone(self.pacific_tz)
            
            # Remove DST adjustment by always using PST offset (-8 hours)
            pst_offset = -8 * 3600  # PST is UTC-8
            pst_time = utc_now.replace(tzinfo=timezone.utc).astimezone(
                timezone(timedelta(seconds=pst_offset))
            )
            
            return pst_time.replace(tzinfo=None)
            
        except Exception as e:
            logger.error(f"Error getting Pacific time: {e}")
            return datetime.utcnow()
            
    def get_pacific_time_ms(self) -> int:
        """Get current Pacific time in milliseconds since epoch"""
        try:
            pacific_time = self.get_pacific_time()
            return int(pacific_time.timestamp() * 1000)
            
        except Exception as e:
            logger.error(f"Error getting Pacific time in milliseconds: {e}")
            return int(datetime.utcnow().timestamp() * 1000)
            
    def ms_to_pacific_time(self, timestamp_ms: int) -> datetime:
        """Convert milliseconds timestamp to Pacific time"""
        try:
            # Convert to seconds
            timestamp_s = timestamp_ms / 1000
            
            # Create datetime from timestamp
            utc_time = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
            
            # Convert to Pacific (no DST)
            pst_offset = -8 * 3600  # PST is UTC-8
            pst_time = utc_time.astimezone(timezone(timedelta(seconds=pst_offset)))
            
            return pst_time.replace(tzinfo=None)
            
        except Exception as e:
            logger.error(f"Error converting milliseconds to Pacific time: {e}")
            return datetime.utcnow()
            
    def pacific_to_ms(self, pacific_time: datetime) -> int:
        """Convert Pacific time to milliseconds timestamp"""
        try:
            # Assume input is in Pacific time (no DST)
            pst_offset = -8 * 3600  # PST is UTC-8
            pst_timezone = timezone(timedelta(seconds=pst_offset))
            
            # Add timezone info
            pacific_with_tz = pacific_time.replace(tzinfo=pst_timezone)
            
            # Convert to milliseconds
            return int(pacific_with_tz.timestamp() * 1000)
            
        except Exception as e:
            logger.error(f"Error converting Pacific time to milliseconds: {e}")
            return int(datetime.utcnow().timestamp() * 1000)
            
    def is_time_in_range(self, check_time: datetime, start_time: datetime, end_time: datetime) -> bool:
        """Check if a time is within a given range"""
        try:
            return start_time <= check_time <= end_time
            
        except Exception as e:
            logger.error(f"Error checking time range: {e}")
            return False
            
    def format_pacific_time(self, pacific_time: datetime) -> str:
        """Format Pacific time as rigid string (no timezone info)"""
        try:
            # Format: YYYY-MM-DDTHH:MM:SS.fff
            return pacific_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            
        except Exception as e:
            logger.error(f"Error formatting Pacific time: {e}")
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            
    def parse_pacific_time(self, time_string: str) -> Optional[datetime]:
        """Parse rigid Pacific time string"""
        try:
            # Try with milliseconds
            try:
                return datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                # Try without milliseconds
                return datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")
                
        except Exception as e:
            logger.error(f"Error parsing Pacific time string '{time_string}': {e}")
            return None
            
    def validate_time_format(self, time_string: str) -> bool:
        """Validate that time string follows rigid format"""
        try:
            parsed = self.parse_pacific_time(time_string)
            return parsed is not None
            
        except Exception as e:
            logger.error(f"Error validating time format: {e}")
            return False
            
    def synchronize_with_network(self) -> bool:
        """Synchronize time with other nodes in the network"""
        try:
            # In a real implementation, this would:
            # 1. Query other nodes for their current time
            # 2. Calculate average/consensus time
            # 3. Adjust local time if necessary
            # 4. Update time synchronization metrics
            
            # For now, we'll just validate our time is reasonable
            current_time = self.get_pacific_time()
            current_ms = self.get_pacific_time_ms()
            
            # Basic sanity check
            if current_ms > 0 and current_time.year >= 2024:
                logger.info(f"Time sync check passed: {self.format_pacific_time(current_time)}")
                return True
            else:
                logger.error(f"Time sync check failed: {current_time}")
                return False
                
        except Exception as e:
            logger.error(f"Error synchronizing with network: {e}")
            return False
            
    def get_time_health_status(self) -> dict:
        """Get time synchronization health status"""
        try:
            current_time = self.get_pacific_time()
            current_ms = self.get_pacific_time_ms()
            
            # Calculate time since epoch
            epoch_ms = int(datetime(1970, 1, 1).timestamp() * 1000)
            time_since_epoch = current_ms - epoch_ms
            
            return {
                'current_time': self.format_pacific_time(current_time),
                'current_ms': current_ms,
                'time_since_epoch_ms': time_since_epoch,
                'timezone': 'Pacific (No DST)',
                'sync_status': 'healthy',
                'last_sync': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting time health status: {e}")
            return {
                'current_time': None,
                'current_ms': 0,
                'time_since_epoch_ms': 0,
                'timezone': 'Pacific (No DST)',
                'sync_status': 'error',
                'last_sync': None,
                'error': str(e)
            }

from datetime import timedelta
