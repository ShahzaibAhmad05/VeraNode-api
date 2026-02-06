import uuid
from datetime import datetime, timedelta
from enum import Enum
from app import db


class AreaEnum(str, Enum):
    SEECS = "SEECS"
    NBS = "NBS"
    ASAB = "ASAB"
    SINES = "SINES"
    SCME = "SCME"
    S3H = "S3H"
    GENERAL = "General"


class VoteTypeEnum(str, Enum):
    FACT = "FACT"
    LIE = "LIE"


class DecisionEnum(str, Enum):
    FACT = "FACT"
    LIE = "LIE"


class Admin(db.Model):
    """Admin account model - stores admin credentials"""
    __tablename__ = 'admins'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'createdAt': self.created_at.isoformat(),
            'lastLogin': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<Admin {self.id[:8]}...>'


class User(db.Model):
    """User account model - stores only registration record and key generation"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    secret_key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'createdAt': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.id[:8]}...>'


class SecretKeyProfile(db.Model):
    """Profile data stored against secret key - untraceable to user account"""
    __tablename__ = 'secret_key_profiles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    secret_key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    area = db.Column(db.Enum(AreaEnum), nullable=False)
    points = db.Column(db.Integer, default=100, nullable=False)
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    rumors = db.relationship('Rumor', back_populates='profile', lazy='dynamic', cascade='all, delete-orphan')
    votes = db.relationship('Vote', back_populates='profile', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'area': self.area.value,
            'points': self.points,
            'isBlocked': self.is_blocked,
            'createdAt': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Profile {self.secret_key[:8]}...>'


class Rumor(db.Model):
    __tablename__ = 'rumors'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    area_of_vote = db.Column(db.Enum(AreaEnum), nullable=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    voting_ends_at = db.Column(db.DateTime, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    is_final = db.Column(db.Boolean, default=False, nullable=False)
    final_decision = db.Column(db.Enum(DecisionEnum), nullable=True)
    nullifier = db.Column(db.String(64), nullable=False, unique=True)  # For privacy
    previous_hash = db.Column(db.String(64), nullable=True)  # Blockchain linkage
    current_hash = db.Column(db.String(64), nullable=False, unique=True)
    profile_id = db.Column(db.String(36), db.ForeignKey('secret_key_profiles.id'), nullable=False)
    
    # Relationships
    profile = db.relationship('SecretKeyProfile', back_populates='rumors')
    votes = db.relationship('Vote', back_populates='rumor', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Rumor, self).__init__(**kwargs)
        if not self.voting_ends_at:
            from app.config import Config
            # Use posted_at if set, otherwise use current time
            posted_time = self.posted_at if self.posted_at else datetime.utcnow()
            self.voting_ends_at = posted_time + timedelta(hours=Config.VOTING_DURATION_HOURS)
            # Ensure posted_at is set
            if not self.posted_at:
                self.posted_at = posted_time
    
    def to_dict(self, include_stats=False):
        data = {
            'id': self.id,
            'content': self.content,
            'areaOfVote': self.area_of_vote.value,
            'postedAt': self.posted_at.isoformat(),
            'votingEndsAt': self.voting_ends_at.isoformat(),
            'isLocked': self.is_locked,
            'isFinal': self.is_final,
            'finalDecision': self.final_decision.value if self.final_decision else None,
            'currentHash': self.current_hash,
            'previousHash': self.previous_hash
        }
        
        # Only show stats when rumor is finalized (prevent psychological influence during voting)
        if include_stats and self.is_final:
            stats = self.get_stats()
            data['stats'] = stats
        elif include_stats and not self.is_final:
            # Return hidden stats during active/locked voting
            data['stats'] = {
                'totalVotes': 'hidden',
                'factVotes': 'hidden',
                'lieVotes': 'hidden',
                'factWeight': 'hidden',
                'lieWeight': 'hidden',
                'underAreaVotes': 'hidden',
                'notUnderAreaVotes': 'hidden',
                'progress': 'hidden'
            }
            
        return data
    
    def get_stats(self):
        """Calculate voting statistics"""
        votes = self.votes.all()
        total_votes = len(votes)
        fact_votes = sum(1 for v in votes if v.vote_type == VoteTypeEnum.FACT)
        lie_votes = sum(1 for v in votes if v.vote_type == VoteTypeEnum.LIE)
        fact_weight = sum(v.weight for v in votes if v.vote_type == VoteTypeEnum.FACT)
        lie_weight = sum(v.weight for v in votes if v.vote_type == VoteTypeEnum.LIE)
        under_area_votes = sum(1 for v in votes if v.is_within_area)
        not_under_area_votes = sum(1 for v in votes if not v.is_within_area)
        
        total_weight = fact_weight + lie_weight
        progress = int((fact_weight / total_weight * 100)) if total_weight > 0 else 0
        
        return {
            'totalVotes': total_votes,
            'factVotes': fact_votes,
            'lieVotes': lie_votes,
            'factWeight': float(fact_weight),
            'lieWeight': float(lie_weight),
            'underAreaVotes': under_area_votes,
            'notUnderAreaVotes': not_under_area_votes,
            'progress': progress
        }
    
    def __repr__(self):
        return f'<Rumor {self.id[:8]}...>'


class Vote(db.Model):
    __tablename__ = 'votes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rumor_id = db.Column(db.String(36), db.ForeignKey('rumors.id'), nullable=False)
    profile_id = db.Column(db.String(36), db.ForeignKey('secret_key_profiles.id'), nullable=False)
    nullifier = db.Column(db.String(64), nullable=False, index=True)  # Hash for anonymity
    vote_type = db.Column(db.Enum(VoteTypeEnum), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    is_within_area = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    rumor = db.relationship('Rumor', back_populates='votes')
    profile = db.relationship('SecretKeyProfile', back_populates='votes')
    
    # Unique constraint: one vote per profile per rumor (enforced by nullifier)
    __table_args__ = (
        db.UniqueConstraint('rumor_id', 'nullifier', name='unique_vote_per_rumor'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'rumorId': self.rumor_id,
            'voteType': self.vote_type.value,
            'weight': float(self.weight),
            'isWithinArea': self.is_within_area,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __repr__(self):
        return f'<Vote {self.vote_type.value} on {self.rumor_id[:8]}...>'


class BlockchainLedger(db.Model):
    """Immutable ledger for finalized rumors - blockchain implementation"""
    __tablename__ = 'blockchain_ledger'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    block_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    previous_block_hash = db.Column(db.String(64), nullable=True)
    rumor_id = db.Column(db.String(36), db.ForeignKey('rumors.id'), nullable=False)
    final_decision = db.Column(db.Enum(DecisionEnum), nullable=False)
    fact_votes = db.Column(db.Integer, nullable=False)
    lie_votes = db.Column(db.Integer, nullable=False)
    total_votes = db.Column(db.Integer, nullable=False)  # Calculated from fact_votes + lie_votes
    fact_weight = db.Column(db.Float, nullable=False)
    lie_weight = db.Column(db.Float, nullable=False)
    under_area_votes = db.Column(db.Integer, nullable=False)  # Votes from within the rumor's area
    not_under_area_votes = db.Column(db.Integer, nullable=False)  # Votes from outside the area
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    block_data = db.Column(db.JSON, nullable=False)  # Complete immutable record
    
    def to_dict(self):
        return {
            'id': self.id,
            'blockHash': self.block_hash,
            'previousBlockHash': self.previous_block_hash,
            'rumorId': self.rumor_id,
            'finalDecision': self.final_decision.value,
            'factVotes': self.fact_votes,
            'lieVotes': self.lie_votes,
            'totalVotes': self.total_votes,
            'factWeight': float(self.fact_weight),
            'lieWeight': float(self.lie_weight),
            'underAreaVotes': self.under_area_votes,
            'notUnderAreaVotes': self.not_under_area_votes,
            'timestamp': self.timestamp.isoformat(),
            'blockData': self.block_data
        }
    
    def __repr__(self):
        return f'<Block #{self.id} {self.block_hash[:8]}...>'
