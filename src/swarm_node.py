import time
from dataclasses import dataclass
from typing import Dict, List, Optional
import hashlib

@dataclass
class PeerScore:
    node_id: str
    success_rate: float = 1.0
    last_seen: float = 0.0
    total_interactions: int = 0
    response_time_ms: float = 0.0

class SwarmNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.peers: Dict[str, PeerScore] = {}
        self.min_reputation = 0.3
        self.decay_factor = 0.95
        self.last_cleanup = time.time()
    
    def update_peer_score(self, peer_id: str, success: bool, response_time_ms: Optional[float] = None) -> None:
        if peer_id not in self.peers:
            self.peers[peer_id] = PeerScore(node_id=peer_id)
        
        peer = self.peers[peer_id]
        peer.total_interactions += 1
        peer.last_seen = time.time()
        
        if success:
            # Weighted average for success rate
            peer.success_rate = (peer.success_rate * peer.total_interactions + 1.0) / (peer.total_interactions + 1)
        else:
            peer.success_rate = (peer.success_rate * peer.total_interactions) / (peer.total_interactions + 1)
            
        if response_time_ms:
            # Exponential moving average for response time
            alpha = 0.1
            peer.response_time_ms = (alpha * response_time_ms + 
                                   (1 - alpha) * peer.response_time_ms)
    
    def get_peer_reputation(self, peer_id: str) -> float:
        if peer_id not in self.peers:
            return 0.0
            
        peer = self.peers[peer_id]
        time_penalty = max(0, 1 - (time.time() - peer.last_seen) / (24 * 3600))
        
        # Combine multiple factors into reputation score
        reputation = (
            0.4 * peer.success_rate +
            0.3 * time_penalty +
            0.3 * min(1.0, 1000 / max(1, peer.response_time_ms))
        )
        return reputation
    
    def get_best_peers(self, n: int = 5) -> List[str]:
        # Clean up stale peers
        self._cleanup_peers()
        
        # Sort peers by reputation
        sorted_peers = sorted(
            self.peers.items(),
            key=lambda x: self.get_peer_reputation(x[0]),
            reverse=True
        )
        
        return [p[0] for p in sorted_peers[:n]]
    
    def _cleanup_peers(self) -> None:
        current_time = time.time()
        if current_time - self.last_cleanup < 3600:  # Run cleanup once per hour
            return
            
        self.last_cleanup = current_time
        stale_peers = [
            peer_id for peer_id, score in self.peers.items()
            if self.get_peer_reputation(peer_id) < self.min_reputation
        ]
        
        for peer_id in stale_peers:
            del self.peers[peer_id]
    
    def get_node_fingerprint(self) -> str:
        """Generate a unique fingerprint for this node based on behavior"""
        data = f"{self.node_id}:{len(self.peers)}:{sum(p.success_rate for p in self.peers.values())}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
