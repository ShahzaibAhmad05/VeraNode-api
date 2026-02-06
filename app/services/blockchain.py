import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from app import db
from app.models import Rumor, BlockchainLedger, DecisionEnum


class BlockchainService:
    """Service to manage blockchain ledger for rumors"""
    
    @staticmethod
    def get_genesis_hash() -> str:
        """Get the genesis (first) block hash"""
        return "0" * 64
    
    @staticmethod
    def get_last_block_hash() -> Optional[str]:
        """Get the hash of the last finalized block"""
        last_block = BlockchainLedger.query.order_by(
            BlockchainLedger.id.desc()
        ).first()
        
        if last_block:
            return last_block.block_hash
        return None
    
    @staticmethod
    def calculate_rumor_hash(
        rumor_id: str,
        content: str,
        final_decision: Optional[str],
        voting_data: str,
        previous_hash: str
    ) -> str:
        """Calculate hash for a rumor in the blockchain"""
        data = f"{rumor_id}{content}{final_decision or ''}{voting_data}{previous_hash}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def create_block(rumor: Rumor) -> BlockchainLedger:
        """Create a new block in the blockchain ledger for a finalized rumor"""
        if not rumor.is_final:
            raise ValueError("Cannot create block for non-finalized rumor")
        
        # Get previous block hash
        previous_hash = BlockchainService.get_last_block_hash()
        if previous_hash is None:
            previous_hash = BlockchainService.get_genesis_hash()
        
        # Calculate statistics
        stats = rumor.get_stats()
        
        # Calculate total_votes from fact_votes + lie_votes
        total_votes = stats['factVotes'] + stats['lieVotes']
        
        # Prepare immutable block data
        block_data = {
            'rumor_id': rumor.id,
            'content': rumor.content,
            'area_of_vote': rumor.area_of_vote.value,
            'posted_at': rumor.posted_at.isoformat(),
            'voting_ended_at': rumor.voting_ends_at.isoformat(),
            'finalized_at': datetime.utcnow().isoformat(),
            'final_decision': rumor.final_decision.value,
            'statistics': stats,
            'profile_id': rumor.profile_id,
            'rumor_nullifier': rumor.nullifier
        }
        
        # Calculate block hash
        voting_data = f"{total_votes}{stats['factVotes']}{stats['lieVotes']}{stats['factWeight']}{stats['lieWeight']}"
        block_hash = BlockchainService.calculate_rumor_hash(
            rumor.id,
            rumor.content,
            rumor.final_decision.value,
            voting_data,
            previous_hash
        )
        
        # Create blockchain entry
        block = BlockchainLedger(
            block_hash=block_hash,
            previous_block_hash=previous_hash,
            rumor_id=rumor.id,
            final_decision=rumor.final_decision,
            fact_votes=stats['factVotes'],
            lie_votes=stats['lieVotes'],
            total_votes=total_votes,
            fact_weight=stats['factWeight'],
            lie_weight=stats['lieWeight'],
            under_area_votes=stats['underAreaVotes'],
            not_under_area_votes=stats['notUnderAreaVotes'],
            block_data=block_data
        )
        
        db.session.add(block)
        
        # Update rumor's current hash
        rumor.current_hash = block_hash
        rumor.previous_hash = previous_hash
        
        return block
    
    @staticmethod
    def verify_chain_integrity() -> tuple[bool, Optional[str]]:
        """Verify the integrity of the entire blockchain"""
        blocks = BlockchainLedger.query.order_by(BlockchainLedger.id.asc()).all()
        
        if not blocks:
            return True, None
        
        # Check first block
        first_block = blocks[0]
        expected_genesis = BlockchainService.get_genesis_hash()
        if first_block.previous_block_hash != expected_genesis:
            return False, f"First block has invalid genesis hash"
        
        # Verify each block links to the previous one
        for i in range(1, len(blocks)):
            current_block = blocks[i]
            previous_block = blocks[i - 1]
            
            if current_block.previous_block_hash != previous_block.block_hash:
                return False, f"Block #{current_block.id} has broken chain link"
        
        return True, None
    
    @staticmethod
    def get_blockchain_stats() -> Dict[str, Any]:
        """Get statistics about the blockchain"""
        total_blocks = BlockchainLedger.query.count()
        fact_decisions = BlockchainLedger.query.filter_by(
            final_decision=DecisionEnum.FACT
        ).count()
        lie_decisions = BlockchainLedger.query.filter_by(
            final_decision=DecisionEnum.LIE
        ).count()
        
        is_valid, error = BlockchainService.verify_chain_integrity()
        
        return {
            'totalBlocks': total_blocks,
            'factDecisions': fact_decisions,
            'lieDecisions': lie_decisions,
            'chainValid': is_valid,
            'chainError': error
        }


def initialize_blockchain():
    """Initialize blockchain - called on app startup"""
    # Nothing specific needed on startup
    # The genesis hash is virtual (all zeros)
    print("Blockchain initialized")


# Export service instance
blockchain_service = BlockchainService()
