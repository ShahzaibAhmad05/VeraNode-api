from datetime import datetime, timedelta
from app import db, scheduler
from app.models import Rumor, Vote, VoteTypeEnum, DecisionEnum
from app.services.ai_service import ai_service
from app.services.blockchain import blockchain_service
from app.config import Config


def lock_expired_voting():
    """Background job to lock voting when time expires and threshold is met"""
    print(f"[{datetime.utcnow()}] Running lock_expired_voting job...")
    
    try:
        # Find rumors that should be locked
        expired_rumors = Rumor.query.filter(
            Rumor.is_locked == False,
            Rumor.voting_ends_at < datetime.utcnow()
        ).all()
        
        locked_count = 0
        for rumor in expired_rumors:
            stats = rumor.get_stats()
            total_votes = stats['totalVotes']
            under_area_votes = stats['underAreaVotes']
            
            # Check if within-area threshold is met (30% by default)
            if total_votes > 0:
                within_area_ratio = under_area_votes / total_votes
                if within_area_ratio >= Config.WITHIN_AREA_THRESHOLD:
                    rumor.is_locked = True
                    locked_count += 1
                    print(f"  - Locked rumor {rumor.id[:8]}... ({within_area_ratio*100:.1f}% within area)")
        
        if locked_count > 0:
            db.session.commit()
            print(f"  ✓ Locked {locked_count} rumor(s)")
        else:
            print(f"  - No rumors to lock")
            
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ Error in lock_expired_voting: {str(e)}")


def finalize_decisions():
    """Background job to finalize decisions and update points"""
    print(f"[{datetime.utcnow()}] Running finalize_decisions job...")
    
    try:
        # Find locked but not finalized rumors
        locked_rumors = Rumor.query.filter(
            Rumor.is_locked == True,
            Rumor.is_final == False
        ).all()
        
        finalized_count = 0
        extended_count = 0
        
        for rumor in locked_rumors:
            stats = rumor.get_stats()
            
            # Prepare data for AI moderation
            moderation_data = {
                'total_votes': stats['totalVotes'],
                'fact_weight': stats['factWeight'],
                'lie_weight': stats['lieWeight'],
                'under_area_votes': stats['underAreaVotes'],
                'content': rumor.content
            }
            
            # Check with AI moderator for anomalies
            ai_decision = ai_service.moderate_decision(moderation_data)
            
            if ai_decision['shouldExtend']:
                # Extend voting by 24 hours
                rumor.voting_ends_at = datetime.utcnow() + timedelta(hours=24)
                rumor.is_locked = False
                extended_count += 1
                print(f"  - Extended voting for rumor {rumor.id[:8]}... Reason: {ai_decision['reason']}")
                continue
            
            # Finalize the decision
            fact_weight = stats['factWeight']
            lie_weight = stats['lieWeight']
            
            if fact_weight > lie_weight:
                rumor.final_decision = DecisionEnum.FACT
            else:
                rumor.final_decision = DecisionEnum.LIE
            
            rumor.is_final = True
            
            # Update points for voters
            votes = rumor.votes.all()
            for vote in votes:
                profile = vote.profile
                if vote.vote_type.value == rumor.final_decision.value:
                    # Correct vote
                    profile.points += Config.CORRECT_VOTE_POINTS
                else:
                    # Incorrect vote
                    profile.points += Config.INCORRECT_VOTE_PENALTY
                
                # Check if profile should be blocked
                if profile.points <= Config.BLOCKING_THRESHOLD:
                    profile.is_blocked = True
            
            # Penalize rumor poster if it's a LIE
            if rumor.final_decision == DecisionEnum.LIE:
                rumor.profile.points += Config.LIE_RUMOR_PENALTY
                if rumor.profile.points <= Config.BLOCKING_THRESHOLD:
                    rumor.profile.is_blocked = True
            
            # Create blockchain block
            try:
                blockchain_service.create_block(rumor)
                print(f"  ✓ Finalized rumor {rumor.id[:8]}... as {rumor.final_decision.value} (blockchain block created)")
                
                # Delete all votes for this rumor (privacy: votes only exist during voting)
                vote_count = len(votes)
                for vote in votes:
                    db.session.delete(vote)
                print(f"  ✓ Deleted {vote_count} vote(s) for rumor {rumor.id[:8]}... (privacy maintained)")
                
            except Exception as e:
                print(f"  ✗ Error creating blockchain block: {str(e)}")
                # Continue anyway, rumor is still finalized
            
            finalized_count += 1
        
        if finalized_count > 0 or extended_count > 0:
            db.session.commit()
            print(f"  ✓ Finalized {finalized_count} rumor(s), Extended {extended_count} rumor(s)")
        else:
            print(f"  - No rumors to finalize")
            
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ Error in finalize_decisions: {str(e)}")


def setup_jobs(app):
    """Setup scheduled background jobs"""
    
    # Add application context to jobs
    def lock_voting_job():
        with app.app_context():
            lock_expired_voting()
    
    def finalize_job():
        with app.app_context():
            finalize_decisions()
    
    # Schedule jobs
    scheduler.add_job(
        func=lock_voting_job,
        trigger='interval',
        minutes=Config.VOTING_CHECK_INTERVAL_MINUTES,
        id='lock_voting',
        name='Lock expired voting',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=finalize_job,
        trigger='interval',
        minutes=Config.FINALIZATION_CHECK_INTERVAL_MINUTES,
        id='finalize_decisions',
        name='Finalize rumor decisions',
        replace_existing=True
    )
    
    print("✓ Background scheduler jobs configured")
    print(f"  - Lock voting check: every {Config.VOTING_CHECK_INTERVAL_MINUTES} minutes")
    print(f"  - Finalization check: every {Config.FINALIZATION_CHECK_INTERVAL_MINUTES} minutes")
