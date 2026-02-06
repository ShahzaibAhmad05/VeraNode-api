# Database Schema - VeraNode API

## Tables Overview

### 1. **admins** (Admin Authentication)
```sql
CREATE TABLE admins (
    id VARCHAR(36) PRIMARY KEY,
    admin_key VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
CREATE INDEX idx_admins_admin_key ON admins(admin_key);
```
**Note:** Admin key is generated once during initialization. Used to access admin dashboard.

### 2. **users** (Registration Record Only)
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    secret_key VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_secret_key ON users(secret_key);
```
**Note:** User's key is their only identifier. No password recovery - if lost, the key cannot be regenerated.

### 3. **secret_key_profiles** (User Data - Zero-Knowledge)
```sql
CREATE TABLE secret_key_profiles (
    id VARCHAR(36) PRIMARY KEY,
    secret_key VARCHAR(64) UNIQUE NOT NULL,
    area VARCHAR(10) NOT NULL,  -- Enum: SEECS, NBS, ASAB, SINES, SCME, S3H, General
    points INTEGER DEFAULT 100 NOT NULL,
    is_blocked BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_profiles_secret_key ON secret_key_profiles(secret_key);
```

### 4. **rumors**
```sql
CREATE TABLE rumors (
    id VARCHAR(36) PRIMARY KEY,
    content TEXT NOT NULL,
    area_of_vote VARCHAR(10) NOT NULL,  -- Enum: SEECS, NBS, ASAB, SINES, SCME, S3H, General
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    voting_ends_at TIMESTAMP NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE NOT NULL,
    is_final BOOLEAN DEFAULT FALSE NOT NULL,
    final_decision VARCHAR(10),  -- Enum: FACT, LIE
    nullifier VARCHAR(64) UNIQUE NOT NULL,
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) UNIQUE NOT NULL,
    profile_id VARCHAR(36) NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES secret_key_profiles(id)
);
```

### 5. **votes** (TEMPORARY - Deleted After Finalization)
```sql
CREATE TABLE votes (
    id VARCHAR(36) PRIMARY KEY,
    rumor_id VARCHAR(36) NOT NULL,
    profile_id VARCHAR(36) NOT NULL,
    nullifier VARCHAR(64) NOT NULL,
    vote_type VARCHAR(10) NOT NULL,  -- Enum: FACT, LIE
    weight FLOAT NOT NULL,
    is_within_area BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (rumor_id) REFERENCES rumors(id),
    FOREIGN KEY (profile_id) REFERENCES secret_key_profiles(id),
    CONSTRAINT unique_vote_per_rumor UNIQUE (rumor_id, nullifier)
);
CREATE INDEX idx_votes_nullifier ON votes(nullifier);
```
⚠️ **IMPORTANT:** Votes are **TEMPORARY** and only exist while voting is active. Once a rumor is finalized and added to the blockchain, **ALL votes for that rumor are permanently deleted** for privacy. Only aggregate statistics are stored in the blockchain ledger.

### 6. **blockchain_ledger** (Immutable Records)
```sql
CREATE TABLE blockchain_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_hash VARCHAR(64) UNIQUE NOT NULL,
    previous_block_hash VARCHAR(64),
    rumor_id VARCHAR(36) NOT NULL,
    final_decision VARCHAR(10) NOT NULL,  -- Enum: FACT, LIE
    fact_votes INTEGER NOT NULL,
    lie_votes INTEGER NOT NULL,
    total_votes INTEGER NOT NULL,  -- Calculated: fact_votes + lie_votes
    fact_weight FLOAT NOT NULL,
    lie_weight FLOAT NOT NULL,
    under_area_votes INTEGER NOT NULL,  -- Votes from within rumor's area
    not_under_area_votes INTEGER NOT NULL,  -- Votes from outside the area
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    block_data JSON NOT NULL,
    FOREIGN KEY (rumor_id) REFERENCES rumors(id)
);
CREATE INDEX idx_blockchain_block_hash ON blockchain_ledger(block_hash);
```

---

## Enums

```python
AreaEnum = ["SEECS", "NBS", "ASAB", "SINES", "SCME", "S3H", "General"]
VoteTypeEnum = ["FACT", "LIE"]
DecisionEnum = ["FACT", "LIE"]
```

---

## Key Relationships

```
users (1) ←→ (1) secret_key_profiles  [via secret_key - NOT FK, just matching value]
    ↑
    └── NO FOREIGN KEY - Zero-Knowledge Design
    
secret_key_profiles (1) → (many) rumors
secret_key_profiles (1) → (many) votes

rumors (1) → (many) votes
rumors (1) ← (1) blockchain_ledger [when finalized]
```

---

## Privacy Architecture

- **users** table: Only stores registration record (secret_key is the user's identifier)
- **secret_key_profiles** table: All user data (area, points, blocking status) stored against secret_key
- **NO direct FK** between `users` and `secret_key_profiles`
- Profile data cannot be traced back to any personal information
- Nullifiers ensure anonymous voting while preventing double-votes
- **Key Loss**: System assumes users will never lose their key - no recovery mechanism exists
- **Admin View**: Admins can ONLY see blocked users' full secret keys (for unblocking), NO area or points visible
- **Vote Privacy**: Votes are DELETED after rumor finalization - cannot trace voting history
- **Blockchain**: Only aggregate statistics stored permanently, individual votes are erased

---

## Export Current Schema (PostgreSQL)

Run to see actual schema:
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print(db.metadata.tables)"
```

Or connect to your database and run:
```sql
\d users
\d secret_key_profiles
\d rumors
\d votes
\d blockchain_ledger
```
