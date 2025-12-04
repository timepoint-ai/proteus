"""
Distributed Storage Service (Phase 13)
IPFS integration for all media and large data storage
"""

import logging
import json
import hashlib
import asyncio
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone
import base64

logger = logging.getLogger(__name__)

try:
    import ipfshttpclient
except ImportError:
    ipfshttpclient = None
    logger.warning("ipfshttpclient not installed - running in mock mode")

class DistributedStorageService:
    """Service for distributed storage using IPFS"""
    
    def __init__(self, ipfs_api_url: str = "/ip4/127.0.0.1/tcp/5001"):
        self.ipfs_api_url = ipfs_api_url
        self.client = None
        self._connect_to_ipfs()
        
        # Local cache for IPFS hashes
        self.cache = {
            'screenshots': {},    # tweet_id -> ipfs_hash
            'market_data': {},   # market_id -> ipfs_hash
            'oracle_proofs': {}, # submission_id -> ipfs_hash
            'analytics': {}      # report_id -> ipfs_hash
        }
        
    def _connect_to_ipfs(self):
        """Connect to IPFS daemon"""
        try:
            if ipfshttpclient:
                self.client = ipfshttpclient.connect(self.ipfs_api_url)
            else:
                self.client = None
            if self.client:
                logger.info(f"Connected to IPFS at {self.ipfs_api_url}")
                
                # Test connection
                node_info = self.client.id()
                logger.info(f"IPFS node ID: {node_info['ID']}")
            else:
                logger.info("Running without IPFS - using mock mode")
            
        except Exception as e:
            logger.warning(f"Could not connect to IPFS: {e}")
            logger.info("Running in offline mode - using mock IPFS")
            self.client = None
            
    def store_screenshot(self, screenshot_data: str, tweet_id: str) -> str:
        """Store screenshot in IPFS"""
        try:
            if not self.client:
                # Mock IPFS hash for development
                mock_hash = f"Qm{hashlib.sha256(screenshot_data.encode()).hexdigest()[:44]}"
                self.cache['screenshots'][tweet_id] = mock_hash
                return mock_hash
                
            # Decode base64 screenshot
            image_data = base64.b64decode(screenshot_data.split(',')[1] if ',' in screenshot_data else screenshot_data)
            
            # Add to IPFS
            result = self.client.add_bytes(image_data)
            ipfs_hash = result
            
            # Pin the content
            self.client.pin.add(ipfs_hash)
            
            # Cache the hash
            self.cache['screenshots'][tweet_id] = ipfs_hash
            
            logger.info(f"Stored screenshot for tweet {tweet_id}: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Error storing screenshot: {e}")
            raise
            
    def retrieve_screenshot(self, ipfs_hash: str) -> Optional[str]:
        """Retrieve screenshot from IPFS"""
        try:
            if not self.client:
                # Return mock data for development
                return f"data:image/png;base64,{ipfs_hash}"
                
            # Get from IPFS
            data = self.client.cat(ipfs_hash)
            
            # Convert to base64
            base64_data = base64.b64encode(data).decode('utf-8')
            return f"data:image/png;base64,{base64_data}"
            
        except Exception as e:
            logger.error(f"Error retrieving screenshot: {e}")
            return None
            
    def store_market_data(self, market_id: str, market_data: Dict) -> str:
        """Store complete market data in IPFS"""
        try:
            if not self.client:
                # Mock IPFS hash
                data_str = json.dumps(market_data, sort_keys=True)
                mock_hash = f"Qm{hashlib.sha256(data_str.encode()).hexdigest()[:44]}"
                self.cache['market_data'][market_id] = mock_hash
                return mock_hash
                
            # Convert to JSON
            json_data = json.dumps(market_data, indent=2)
            
            # Add to IPFS
            result = self.client.add_json(market_data)
            ipfs_hash = result
            
            # Pin the content
            self.client.pin.add(ipfs_hash)
            
            # Cache the hash
            self.cache['market_data'][market_id] = ipfs_hash
            
            logger.info(f"Stored market data for {market_id}: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
            raise
            
    def retrieve_market_data(self, ipfs_hash: str) -> Optional[Dict]:
        """Retrieve market data from IPFS"""
        try:
            if not self.client:
                # Return mock data
                return {
                    'market_id': 'mock_market',
                    'ipfs_hash': ipfs_hash,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
            # Get from IPFS
            data = self.client.get_json(ipfs_hash)
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            return None
            
    def store_oracle_proof(self, submission_id: str, proof_data: Dict) -> str:
        """Store oracle validation proof in IPFS"""
        try:
            # Add metadata
            proof_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            proof_data['submission_id'] = submission_id
            
            if not self.client:
                # Mock IPFS hash
                data_str = json.dumps(proof_data, sort_keys=True)
                mock_hash = f"Qm{hashlib.sha256(data_str.encode()).hexdigest()[:44]}"
                self.cache['oracle_proofs'][submission_id] = mock_hash
                return mock_hash
                
            # Add to IPFS
            result = self.client.add_json(proof_data)
            ipfs_hash = result
            
            # Pin the content
            self.client.pin.add(ipfs_hash)
            
            # Cache the hash
            self.cache['oracle_proofs'][submission_id] = ipfs_hash
            
            logger.info(f"Stored oracle proof for {submission_id}: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Error storing oracle proof: {e}")
            raise
            
    def store_analytics_report(self, report_type: str, report_data: Dict) -> str:
        """Store analytics report in IPFS"""
        try:
            report_id = f"{report_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            
            if not self.client:
                # Mock IPFS hash
                data_str = json.dumps(report_data, sort_keys=True)
                mock_hash = f"Qm{hashlib.sha256(data_str.encode()).hexdigest()[:44]}"
                self.cache['analytics'][report_id] = mock_hash
                return mock_hash
                
            # Add to IPFS
            result = self.client.add_json(report_data)
            ipfs_hash = result
            
            # Pin the content
            self.client.pin.add(ipfs_hash)
            
            # Cache the hash
            self.cache['analytics'][report_id] = ipfs_hash
            
            logger.info(f"Stored analytics report {report_id}: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Error storing analytics report: {e}")
            raise
            
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        stats = {
            'screenshots': len(self.cache['screenshots']),
            'market_data': len(self.cache['market_data']),
            'oracle_proofs': len(self.cache['oracle_proofs']),
            'analytics': len(self.cache['analytics']),
            'total_objects': sum(len(cache) for cache in self.cache.values())
        }
        
        if self.client:
            try:
                # Get IPFS repo stats
                repo_stat = self.client.repo.stat()
                stats['ipfs_repo_size'] = repo_stat['RepoSize']
                stats['ipfs_num_objects'] = repo_stat['NumObjects']
            except:
                pass
                
        return stats
        
    def pin_content(self, ipfs_hash: str) -> bool:
        """Pin content to ensure it stays available"""
        try:
            if not self.client:
                return True
                
            self.client.pin.add(ipfs_hash)
            logger.info(f"Pinned content: {ipfs_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error pinning content: {e}")
            return False
            
    def unpin_content(self, ipfs_hash: str) -> bool:
        """Unpin content to allow garbage collection"""
        try:
            if not self.client:
                return True
                
            self.client.pin.rm(ipfs_hash)
            logger.info(f"Unpinned content: {ipfs_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error unpinning content: {e}")
            return False
            
    def get_pinned_content(self) -> List[str]:
        """Get list of all pinned content"""
        try:
            if not self.client:
                return list(set(
                    list(self.cache['screenshots'].values()) +
                    list(self.cache['market_data'].values()) +
                    list(self.cache['oracle_proofs'].values()) +
                    list(self.cache['analytics'].values())
                ))
                
            pins = self.client.pin.ls(type='recursive')
            return [pin['Hash'] for pin in pins['Keys'].values()]
            
        except Exception as e:
            logger.error(f"Error getting pinned content: {e}")
            return []