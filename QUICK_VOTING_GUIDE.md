# Quick Voting Guide - ✅ FIXED & TESTED

**Backend Issue RESOLVED**: Vote weight calculation error fixed. Restart Flask server to load changes.

## ✅ Authentication Setup (REQUIRED)

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: { 'Content-Type': 'application/json' }
});

// MUST HAVE THIS INTERCEPTOR
api.interceptors.request.use((config) => {
  const secretKey = localStorage.getItem('secretKey');
  if (secretKey) {
    config.headers['X-Secret-Key'] = secretKey;
  }
  return config;
});

export default api;
```

---

## Cast Vote

```typescript
// POST /api/voting/vote
const response = await api.post('/voting/vote', {
  rumorId: 'rumor-uuid',
  voteType: 'FACT' // or 'LIE'
});

// Returns:
{
  message: "Vote recorded successfully",
  vote: {
    rumorId: "uuid",
    voteType: "FACT",
    weight: 1.0,
    isWithinArea: true,
    timestamp: "2026-02-07T12:00:00"
  }
}
```

---

## Check if Voted

```typescript
// GET /api/voting/status/{rumorId}
const response = await api.get(`/voting/status/${rumorId}`);

// Returns:
{
  hasVoted: true,
  rumorId: "uuid"
}
```

---

## Common Errors

| Error | Meaning | Fix |
|-------|---------|-----|
| 401 UNAUTHORIZED | No X-Secret-Key header | Add interceptor (see above) |
| 401 INVALID_SECRET_KEY | Wrong secret key | Check localStorage has correct key |
| 400 DUPLICATE_VOTE | Already voted | Disable vote button, show "Already voted" |
| 400 VOTING_CLOSED | Rumor locked | Show "Voting closed" |
| 404 RUMOR_NOT_FOUND | Bad rumor ID | Check rumor exists |

---

## Complete Example

```typescript
const VotingComponent = ({ rumorId }: { rumorId: string }) => {
  const [hasVoted, setHasVoted] = useState(false);
  
  useEffect(() => {
    // Check if already voted
    api.get(`/voting/status/${rumorId}`)
      .then(res => setHasVoted(res.data.hasVoted));
  }, [rumorId]);
  
  const handleVote = async (voteType: 'FACT' | 'LIE') => {
    try {
      await api.post('/voting/vote', { rumorId, voteType });
      setHasVoted(true);
      alert('Vote recorded!');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to vote');
    }
  };
  
  if (hasVoted) return <div>Already voted</div>;
  
  return (
    <div>
      <button onClick={() => handleVote('FACT')}>FACT</button>
      <button onClick={() => handleVote('LIE')}>LIE</button>
    </div>
  );
};
```

---

## Debug Checklist

1. ✅ Interceptor added to axios?
2. ✅ `secretKey` exists in localStorage?
3. ✅ Network tab shows `X-Secret-Key` header?
4. ✅ Backend running on port 5000?
5. ✅ Rumor exists and not locked?
