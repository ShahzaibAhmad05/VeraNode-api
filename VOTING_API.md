# Voting API - Frontend Guide

## ⚠️ CRITICAL: Authentication Required

**ALL voting endpoints require the `X-Secret-Key` header.**

If you get **401 Unauthorized**, the secret key is missing or invalid.

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

**Without this interceptor, all voting requests will fail with 401.**

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
- **401 UNAUTHORIZED**: Missing or invalid X-Secret-Key header
- **400 DUPLICATE_VOTE**: User already voted on this rumor
- **400 VOTING_CLOSED**: Rumor is locked, no more votes accepted
- **400 VOTING_ENDED**: Voting period ended (not locked yet)
- **400 INVALID_VOTE_TYPE**: voteType must be "FACT" or "LIE"
- **404 RUMOR_NOT_FOUND**: Rumor doesn't exist

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
- **401 UNAUTHORIZED**: Missing or invalid X-Secret-Key header
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
- **401 UNAUTHORIZED**: Missing or invalid X-Secret-Key header
- **404 PROFILE_NOT_FOUND**: Secret key doesn't match any profile

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

## Troubleshooting 401 Unauthorized

### Problem
```
Request failed with status code 401
```

### Solution Checklist

1. **Add Secret Key to Headers**
   ```typescript
   // Option 1: Axios interceptor (recommended)
   api.interceptors.request.use((config) => {
     const secretKey = localStorage.getItem('secretKey');
     if (secretKey) {
       config.headers['X-Secret-Key'] = secretKey;
     }
     return config;
   });
   ```

2. **OR Manual Header per Request**
   ```typescript
   const secretKey = localStorage.getItem('secretKey');
   await api.post('/voting/vote', 
     { rumorId, voteType },
     { headers: { 'X-Secret-Key': secretKey } }
   );
   ```

3. **Verify Secret Key Exists**
   ```typescript
   const secretKey = localStorage.getItem('secretKey');
   if (!secretKey) {
     // Redirect to login or registration
     console.error('No secret key found');
   }
   ```

4. **Test with cURL**
   ```bash
   curl -X POST http://localhost:5000/api/voting/vote \
     -H "Content-Type: application/json" \
     -H "X-Secret-Key: your-secret-key-here" \
     -d '{"rumorId":"rumor-uuid","voteType":"FACT"}'
   ```

### Common Mistakes

❌ **Wrong**: Headers not sent
```typescript
api.post('/voting/vote', { rumorId, voteType });
```

✅ **Correct**: Headers included
```typescript
api.post('/voting/vote', { rumorId, voteType }, {
  headers: { 'X-Secret-Key': secretKey }
});
```

❌ **Wrong**: Header name typo
```typescript
headers: { 'Secret-Key': secretKey }  // Missing X-
```

✅ **Correct**: Exact header name
```typescript
headers: { 'X-Secret-Key': secretKey }
```
