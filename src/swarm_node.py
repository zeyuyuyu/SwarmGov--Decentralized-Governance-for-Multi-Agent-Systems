import time
import hashlib
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Message:
    sender: str
    proposal: Any
    signature: str
    timestamp: float

class SwarmNode:
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.proposals: Dict[str, Any] = {}
        self.votes: Dict[str, Dict[str, bool]] = {}
        self.committed: Dict[str, Any] = {}
        self.round = 0
        
    def create_proposal(self, proposal: Any) -> Message:
        """Create a signed proposal message"""
        timestamp = time.time()
        msg_hash = hashlib.sha256(f"{self.node_id}{proposal}{timestamp}".encode()).hexdigest()
        return Message(
            sender=self.node_id,
            proposal=proposal,
            signature=msg_hash,
            timestamp=timestamp
        )
    
    def receive_proposal(self, message: Message) -> bool:
        """Process received proposal and vote"""
        if not self._verify_message(message):
            return False
            
        proposal_id = message.signature
        if proposal_id not in self.proposals:
            self.proposals[proposal_id] = message.proposal
            self.votes[proposal_id] = {}
        
        # Vote on proposal
        vote = self._validate_proposal(message.proposal)
        self.votes[proposal_id][self.node_id] = vote
        return vote

    def check_consensus(self, proposal_id: str) -> bool:
        """Check if consensus is reached for a proposal"""
        if proposal_id not in self.votes:
            return False
            
        total_votes = len(self.votes[proposal_id])
        positive_votes = sum(1 for v in self.votes[proposal_id].values() if v)
        
        # Require 2/3 majority for Byzantine fault tolerance
        if total_votes >= len(self.peers) * 2/3:
            if positive_votes >= total_votes * 2/3:
                self._commit_proposal(proposal_id)
                return True
        return False

    def _verify_message(self, message: Message) -> bool:
        """Verify message authenticity"""
        expected_hash = hashlib.sha256(
            f"{message.sender}{message.proposal}{message.timestamp}".encode()
        ).hexdigest()
        return message.signature == expected_hash

    def _validate_proposal(self, proposal: Any) -> bool:
        """Custom validation logic for proposals"""
        # Implement domain-specific validation
        return True

    def _commit_proposal(self, proposal_id: str) -> None:
        """Commit an accepted proposal"""
        if proposal_id in self.proposals and proposal_id not in self.committed:
            self.committed[proposal_id] = self.proposals[proposal_id]
            self.round += 1

    def get_committed_proposals(self) -> Dict[str, Any]:
        """Return all committed proposals"""
        return self.committed.copy()

    def get_current_round(self) -> int:
        """Return current consensus round"""
        return self.round
