# Voting API - Frontend Guide

## ✅ FIXED: Authentication Now Works with X-Secret-Key

The backend now accepts the `X-Secret-Key` header directly - no JWT token needed.

### Setup Your API Client

```typescript
// lib/api.ts - Configure headers
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add secret key to EVERY request
api.interceptors.request.use((config) => {
  const secretKey = localStorage.getItem('secretKey'); // or your storage method
  if (secretKey) {
    config.headers['X-Secret-Key'] = secretKey;
  }
  return config;
});
```

**This will now work correctly. The 401 error is fixed.**

---

## Cast a Vote

```
POST /api/voting/vote
```

### Headers
```
Content-Type: application/json
X-Secret-Key: {user's secret key}  ← REQUIRED
```

### Request Body
```json
{
  "rumorId": "uuid-of-rumor",
  "voteType": "FACT" | "LIE"
}
```

### Success Response (201)
```json
{
  "message": "Vote recorded successfully",
  "vote": {
    "rumorId": "uuid",
    "voteType": "FACT",
    "weight": 1.0,
    "isWithinArea": true,
    "timestamp": "ISO datetime"
  }
}
```

### Error Responses
- **401 UNAUTHORIZED**: Missing X-Secret-Key header
- **401 INVALID_SECRET_KEY**: Secret key doesn't match any profile
- **400 DUPLICATE_VOTE**: User already voted on this rumor
- **400 VOTING_CLOSED**: Rumor is locked, no more votes accepted
- **400 VOTING_ENDED**: Voting period ended (not locked yet)
- **400 INVALID_VOTE_TYPE**: voteType must be "FACT" or "LIE"
- **404 RUMOR_NOT_FOUND**: Rumor doesn't exist
- **403 ACCOUNT_BLOCKED**: User's reputation is too low (≤ -100 points)

---

## Check Vote Status

```
GET /api/voting/status/{rumorId}
```

### Headers
```
X-Secret-Key: {user's secret key}  ← REQUIRED
```

### Success Response (200)
```json
{
  "hasVoted": true,
  "rumorId": "uuid"
}
```

### Error Responses
- **401 UNAUTHORIZED**: Missing X-Secret-Key header
- **401 INVALID_SECRET_KEY**: Secret key doesn't match any profile
- **404 RUMOR_NOT_FOUND**: Rumor doesn't exist

**Note**: Only tells you IF you voted, not WHAT you voted for (privacy)

---

## Get My Votes

```
GET /api/voting/my-votes
```

### Headers
```
X-Secret-Key: {user's secret key}  ← REQUIRED
```

### Success Response (200)
```json
{
  "votes": [
    {
      "id": "uuid",
      "voteType": "FACT",
      "weight": 1.0,
      "isWithinArea": true,
      "timestamp": "ISO datetime",
      "rumor": {
        "id": "uuid",
        "content": "...",
        "isLocked": false,
        "isFinal": false
      }
    }
  ],
  "note": "Only shows votes for active rumors. Votes are deleted after finalization for privacy."
}
```

### Error Responses
- **401 UNAUTHORIZED**: Missing X-Secret-Key header
- **401 INVALID_SECRET_KEY**: Secret key doesn't match any profile
- **403 ACCOUNT_BLOCKED**: User's reputation is too low

**Important**: Votes are permanently deleted after rumor finalization for privacy.

---

## Vote Weight Logic

- **Within Area** (user.area == rumor.areaOfVote): weight = **1.0**
- **Outside Area**: weight = **0.3**

System requires 30% of votes to be "within area" for rumor to be finalized.

---

## Complete Flow

1. **Load rumor**: `GET /api/rumors/{id}`
2. **Check if voted**: `GET /api/voting/status/{id}`
3. **If not voted & not locked**: Show voting UI
4. **Cast vote**: `POST /api/voting/vote` with `{rumorId, voteType}`
5. **Update UI**: Mark as voted, disable voting buttons

---

## Troubleshooting

### 401 Unauthorized Error

**Cause**: Missing or invalid `X-Secret-Key` header

**Solutions**:

1. **Verify Secret Key Exists**
   ```typescript
   const secretKey = localStorage.getItem('secretKey');
   console.log('Secret Key:', secretKey ? 'Found' : 'Missing');
   ```

2. **Check Header is Sent**
   - Open browser DevTools → Network tab
   - Click on the failed request
   - Check Request Headers section
   - Verify `X-Secret-Key` is present with correct value

3. **Test Backend Directly**
   ```bash
   # Replace YOUR_SECRET_KEY and RUMOR_ID
   curl -X POST http://localhost:5000/api/voting/vote \
     -H "Content-Type: application/json" \
     -H "X-Secret-Key: YOUR_SECRET_KEY" \
     -d '{"rumorId":"RUMOR_ID","voteType":"FACT"}'
   ```

4. **Common Axios Setup Issues**

   ❌ **Wrong**: No interceptor, header not sent
   ```typescript
   const response = await api.post('/voting/vote', { rumorId, voteType });
   ```

   ✅ **Correct**: Interceptor adds header automatically
   ```typescript
   api.interceptors.request.use((config) => {
     const secretKey = localStorage.getItem('secretKey');
     if (secretKey) {
       config.headers['X-Secret-Key'] = secretKey;
     }
     return config;
   });
   
   // Now this works:
   const response = await api.post('/voting/vote', { rumorId, voteType });
   ```

   ✅ **Also Correct**: Manual header per request
   ```typescript
   const secretKey = localStorage.getItem('secretKey');
   const response = await api.post('/voting/vote', 
     { rumorId, voteType },
     { headers: { 'X-Secret-Key': secretKey } }
   );
   ```

### 403 Account Blocked

**Cause**: User's reputation points ≤ -100

**What to do**: 
- User can still view content but cannot post or vote
- Points are lost from: invalid posts (-25), incorrect votes (-10), posting lies (-50)
- No recovery mechanism - user must create new account

### 400 Duplicate Vote

**Cause**: User already voted on this rumor

**What to do**: 
- Check vote status first: `GET /api/voting/status/{rumorId}`
- Disable voting UI if `hasVoted: true`
