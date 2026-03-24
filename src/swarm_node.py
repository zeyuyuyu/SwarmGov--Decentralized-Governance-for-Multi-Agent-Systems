import asyncio
from dataclasses import dataclass
from typing import List, Dict, Callable
from enum import Enum
import time

class VoteType(Enum):
    YES = 1
    NO = 0
    ABSTAIN = -1

@dataclass
class Proposal:
    id: str
    description: str
    action: Callable
    timestamp: float
    votes: Dict[str, VoteType]
    executed: bool
    min_votes: int
    expiration: float

class SwarmNode:
    def __init__(self, node_id: str, peers: List[str] = None):
        self.node_id = node_id
        self.peers = peers or []
        self.proposals: Dict[str, Proposal] = {}
        self.state = {}
        self.min_consensus_ratio = 0.67

    async def submit_proposal(self, description: str, action: Callable, expiration_seconds: int = 300) -> str:
        proposal_id = f'prop_{int(time.time())}_{self.node_id}'
        self.proposals[proposal_id] = Proposal(
            id=proposal_id,
            description=description,
            action=action,
            timestamp=time.time(),
            votes={self.node_id: VoteType.YES},
            executed=False,
            min_votes=max(len(self.peers) // 2 + 1, 2),
            expiration=time.time() + expiration_seconds
        )
        await self.broadcast_proposal(proposal_id)
        return proposal_id

    async def vote(self, proposal_id: str, vote: VoteType) -> bool:
        if proposal_id not in self.proposals:
            return False
            
        proposal = self.proposals[proposal_id]
        if time.time() > proposal.expiration:
            return False

        proposal.votes[self.node_id] = vote
        await self.check_and_execute_proposal(proposal_id)
        return True

    async def check_and_execute_proposal(self, proposal_id: str) -> bool:
        proposal = self.proposals[proposal_id]
        if proposal.executed:
            return False

        yes_votes = sum(1 for v in proposal.votes.values() if v == VoteType.YES)
        total_votes = len(proposal.votes)

        if yes_votes >= proposal.min_votes and \\
           yes_votes / total_votes >= self.min_consensus_ratio:
            try:
                proposal.action()
                proposal.executed = True
                return True
            except Exception as e:
                print(f'Error executing proposal {proposal_id}: {str(e)}')
        return False

    async def broadcast_proposal(self, proposal_id: str):
        # In a real implementation, this would use network communication
        # to broadcast the proposal to all peers
        pass

    async def sync_state(self):
        # Implement state synchronization between nodes
        pass

    def get_proposal_status(self, proposal_id: str) -> Dict:
        if proposal_id not in self.proposals:
            return {}

        prop = self.proposals[proposal_id]
        return {
            'id': prop.id,
            'description': prop.description,
            'votes_yes': sum(1 for v in prop.votes.values() if v == VoteType.YES),
            'votes_no': sum(1 for v in prop.votes.values() if v == VoteType.NO),
            'votes_abstain': sum(1 for v in prop.votes.values() if v == VoteType.ABSTAIN),
            'executed': prop.executed,
            'expired': time.time() > prop.expiration
        }

    async def cleanup_expired_proposals(self):
        current_time = time.time()
        expired = [pid for pid, p in self.proposals.items() 
                  if current_time > p.expiration and not p.executed]
        for pid in expired:
            del self.proposals[pid]
