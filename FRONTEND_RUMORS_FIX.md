# Frontend Rumors Loading Fix

## API Endpoint
```
GET /api/rumors
```

## Request Headers
```
Content-Type: application/json
```

**NO AUTHENTICATION REQUIRED** - This is a public endpoint

## Response Structure
```json
{
  "rumors": [
    {
      "id": "uuid",
      "content": "string",
      "areaOfVote": "POLITICS|SPORTS|ENTERTAINMENT|TECH|HEALTH|FINANCE",
      "postedAt": "ISO datetime",
      "votingEndsAt": "ISO datetime",
      "isLocked": boolean,
      "isFinal": boolean,
      "finalDecision": "FACT|LIE|null",
      "currentHash": "string",
      "previousHash": "string",
      "stats": {
        // "hidden" during voting, actual numbers when isFinal=true
      }
    }
  ]
}
```

## Common Issues

### 1. Wrong URL
❌ `/rumors` 
✅ `/api/rumors`

### 2. CORS Error
- Ensure your frontend URL is in backend's allowed origins
- Backend returns CORS headers automatically

### 3. Response Handling
```javascript
// Correct
const response = await fetch('/api/rumors');
const data = await response.json();
const rumorsList = data.rumors; // Array of rumors

// Wrong - rumors is NOT the root
const rumorsList = data; // This fails
```

### 4. Optional Filters
```
GET /api/rumors?status=active   // Only active rumors
GET /api/rumors?status=locked   // Only locked rumors
GET /api/rumors?status=final    // Only finalized rumors
```

### 5. Empty Response
If `rumors: []` is returned, the database is empty. Run:
```bash
python fresh_start.py
```

## Quick Test
```bash
curl http://localhost:5000/api/rumors
```

Should return `{"rumors": [...]}` with array of rumors.
