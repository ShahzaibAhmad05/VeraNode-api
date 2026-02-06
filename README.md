# VeraNode Backend API

A production-ready Flask backend for VeraNode - a blockchain-based rumor verification platform for university communities.

## 🚀 Features

- **Application Factory Pattern** with Flask Blueprints
- **PostgreSQL Database** with SQLAlchemy ORM
- **JWT Authentication** for secure user sessions
- **Blockchain Ledger** with SHA-256 hashing for immutable records
- **Deterministic Nullifiers** using middleware to prevent double-voting
- **AI-Powered Validation** with OpenAI/Anthropic integration
- **Weighted Voting System** based on user reputation and area proximity
- **Background Scheduler** for automated decision finalization
- **CORS Support** for frontend integration
- **Comprehensive Error Handling**

## 📋 Requirements

- Python 3.9+
- PostgreSQL 12+
- OpenAI API Key (optional, for AI validation)

## 🛠️ Installation

### 1. Clone the repository

```bash
cd VeraNode-api
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL database

```bash
# Create database
createdb veranode

# Or using psql
psql -U postgres
CREATE DATABASE veranode;
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and update the following:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/veranode
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
OPENAI_API_KEY=sk-your-openai-api-key-here
CORS_ORIGINS=http://localhost:3000
PORT=3008
```

### 6. Initialize database

```bash
python run.py
```

The database tables will be created automatically on first run.

## 🏃 Running the Application

### Development Mode

```bash
python run.py
```

The API will be available at `http://localhost:3008`

### Production Mode with Gunicorn

```bash
gunicorn --bind 0.0.0.0:3008 --workers 4 "app:create_app()"
```

## 📚 API Documentation

### Base URL: `http://localhost:3008/api`

### Authentication Endpoints

#### POST `/api/auth/register`
Register a new user.

**Request:**
```json
{
  "universityId": "21i-1234",
  "password": "securepassword",
  "area": "SEECS"
}
```

**Response:**
```json
{
  "user": {...},
  "token": "JWT_TOKEN",
  "secretKey": "64-char-hex-key"
}
```

#### POST `/api/auth/login`
Login existing user.

**Request:**
```json
{
  "universityId": "21i-1234",
  "password": "securepassword"
}
```

#### GET `/api/auth/verify`
Verify JWT token.

**Headers:** `Authorization: Bearer <token>`

### Rumor Endpoints

#### POST `/api/rumors/validate`
Validate rumor with AI before posting.

**Request:**
```json
{
  "content": "Rumor text here"
}
```

#### POST `/api/rumors`
Create a new rumor.

**Request:**
```json
{
  "content": "Rumor text",
  "areaOfVote": "SEECS"
}
```

#### GET `/api/rumors`
Get list of rumors.

**Query Parameters:**
- `area` - Filter by area (SEECS, NBS, etc.)
- `status` - Filter by status (active, locked, final)

#### GET `/api/rumors/:id`
Get single rumor details.

#### GET `/api/rumors/:id/stats`
Get rumor voting statistics.

### Voting Endpoints

#### POST `/api/rumors/:id/vote`
Vote on a rumor.

**Request:**
```json
{
  "voteType": "FACT"
}
```

#### GET `/api/rumors/:id/vote-status`
Check if user voted on a rumor.

#### GET `/api/votes/my-votes`
Get all votes by current user.

### User Endpoints

#### GET `/api/user/stats`
Get user statistics.

#### GET `/api/user/rumors`
Get all rumors posted by user.

#### GET `/api/user/profile`
Get user profile.

## 🏗️ Project Structure

```
VeraNode-api/
├── app/
│   ├── __init__.py              # Application factory
│   ├── config.py                # Configuration
│   ├── models.py                # Database models
│   ├── blueprints/
│   │   ├── auth.py              # Authentication routes
│   │   ├── rumors.py            # Rumor management routes
│   │   ├── voting.py            # Voting routes
│   │   └── users.py             # User routes
│   ├── middleware/
│   │   └── nullifier.py         # Nullifier middleware
│   ├── services/
│   │   ├── ai_service.py        # AI validation service
│   │   ├── blockchain.py        # Blockchain service
│   │   └── scheduler.py         # Background jobs
│   └── utils/
│       ├── validators.py        # Input validators
│       ├── helpers.py           # Helper functions
│       └── error_handlers.py    # Error handlers
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 🔒 Security Features

- **Password Hashing**: bcrypt for secure password storage
- **JWT Tokens**: Secure authentication with 30-day expiry
- **Deterministic Nullifiers**: Privacy-preserving vote tracking
- **Secret Keys**: 64-character hex keys for each user
- **Blocked Users**: Automatic blocking at -100 points

## ⚙️ Configuration

### Areas (Universities/Schools)
- SEECS - School of Electrical Engineering & Computer Science
- NBS - NUST Business School
- ASAB - Atta-ur-Rahman School of Applied Biosciences
- SINES - School of Natural Sciences
- SCME - School of Civil & Environmental Engineering
- S3H - School of Social Sciences & Humanities
- General - General campus rumors

### Points System
- Initial points: 100
- Correct vote: +10 points
- Incorrect vote: -5 points
- Posting a LIE: -50 points
- Blocking threshold: -100 points

### Voting Rules
- Voting duration: 48 hours
- Within-area threshold: 30% of votes
- Within-area multiplier: 1.5x
- Outside-area multiplier: 0.5x

## 🤖 Background Jobs

### Lock Voting (Every 5 minutes)
- Locks voting when 48 hours expire
- Checks within-area threshold (30%)

### Finalize Decisions (Every 10 minutes)
- AI moderation for anomaly detection
- Calculates final decision (FACT/LIE)
- Updates user points
- Creates blockchain block

## 🔗 Blockchain Implementation

Each finalized rumor is added to an immutable blockchain ledger:
- **Genesis Hash**: All zeros (virtual first block)
- **Block Hash**: SHA-256 of (rumor_id + content + decision + voting_data + previous_hash)
- **Chain Verification**: Each block links to the previous one
- **Immutable Records**: Complete voting history stored

## 🧪 Testing

### Health Check
```bash
curl http://localhost:3008/api/health
```

### Register User
```bash
curl -X POST http://localhost:3008/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"universityId":"21i-1234","password":"test1234","area":"SEECS"}'
```

## 🚢 Deployment

### Environment Variables for Production
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/db
JWT_SECRET=long-random-secret-key
OPENAI_API_KEY=sk-...
```

### Using Gunicorn
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 4 "app:create_app('production')"
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:3008", "--workers", "4", "app:create_app()"]
```

## 📝 License

MIT License

## 👥 Contributors

VeraNode Development Team

## 🐛 Error Codes

- `INVALID_CREDENTIALS` - Login failed
- `ALREADY_VOTED` - User already voted on rumor
- `VOTING_CLOSED` - Rumor voting is locked
- `INVALID_RUMOR` - AI rejected rumor
- `INSUFFICIENT_POINTS` - User blocked
- `ACCOUNT_BLOCKED` - Account blocked due to low points

## 📞 Support

For issues and questions, please open an issue on GitHub.
