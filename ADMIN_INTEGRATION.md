# Frontend Integration - Admin System

## Admin Private Key System

The admin dashboard uses a **private key authentication system** similar to user secret keys. The admin key is generated once during database initialization and must be saved securely.

---

## Admin Login

**Endpoint:** `POST /api/admin/login`

**Request:**
```json
{
  "adminKey": "6cb85cd49b6fb4f02f849574337ffc5c4726f11822b32c31e0794a385a0cace8"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "admin": {
    "id": "abc123...",
    "createdAt": "2026-02-07T10:30:00.000Z",
    "lastLogin": "2026-02-07T12:00:00.000Z"
  }
}
```

**Frontend Implementation:**
- Create admin login page at `/admin/login`
- Input field for admin private key (64-character hex string)
- Store admin token separately from user token
- Redirect to admin dashboard on success

---

## Admin Dashboard Endpoints

**All endpoints require admin authentication:** Include `Authorization: Bearer <admin_token>` header

### 1. Get Blocked Users

**Endpoint:** `GET /api/admin/dashboard/blocked-users`

**Response:**
```json
{
  "blockedProfiles": [
    {
      "secretKey": "5fdd9cf8395836dbfb348a75a1f17b85df2f0e3f0ba53dede53c8cc66b76ed9b",
      "isBlocked": true,
      "createdAt": "2026-01-15T08:30:00.000Z"
    }
  ],
  "count": 1
}
```

**Display:**
- Table: Full Secret Key | Created At | Actions
- Show FULL secret key (64 characters) for easy copying
- "Unblock" button for each blocked user
- **NO area or points shown** (privacy - admins only manage blocking, not user data)

---

### 2. Unblock User

**Endpoint:** `POST /api/admin/dashboard/unblock-user`

**Request:**
```json
{
  "secretKey": "5fdd9cf8395836dbfb348a75a1f17b85df2f0e3f0ba53dede53c8cc66b76ed9b"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile unblocked successfully",
  "profile": {
    "secretKey": "5fdd9cf8395836dbfb348a75a1f17b85df2f0e3f0ba53dede53c8cc66b76ed9b",
    "isBlocked": false
  }
}
```

**Implementation:**
- Show confirmation dialog before unblocking
- Refresh blocked users list after success
- Display success toast/notification

---

### 3. Dashboard Statistics

**Endpoint:** `GET /api/admin/dashboard/stats`

**Response:**
```json
{
  "users": {
    "total": 150,
    "totalProfiles": 150,
    "active": 145,
    "blocked": 5
  },
  "rumors": {
    "total": 250,
    "active": 45,
    "finalized": 205
  },
  "votes": {
    "active": 320
  },
  "blockchain": {
    "totalBlocks": 205
  }
}
```

**Display:**
- Dashboard overview with stat cards:
  - Users: Total, Active, Blocked
  - Rumors: Total, Active, Finalized
  - Active Votes count
  - Blockchain Blocks count

---

### 4. Verify Admin

**Endpoint:** `GET /api/admin/verify`

**Response:**
```json
{
  "success": true,
  "admin": {
    "id": "abc123...",
    "createdAt": "2026-02-07T10:30:00.000Z",
    "lastLogin": "2026-02-07T12:00:00.000Z"
  }
}
```

**Usage:**
- Verify admin token on dashboard page load
- Redirect to login if invalid/expired

---

## Frontend Structure

### Recommended Routes

1. **`/admin/login`** - Admin login page
2. **`/admin/dashboard`** - Statistics overview
3. **`/admin/blocked-users`** - List and manage blocked users

### Route Protection

```javascript
// Example route guard
const requireAdmin = () => {
  const adminToken = getAdminToken();
  if (!adminToken) {
    redirect('/admin/login');
    return false;
  }
  
  // Verify token
  const response = await fetch('/api/admin/verify', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  
  if (!response.ok) {
    redirect('/admin/login');
    return false;
  }
  
  return true;
};
```

### Security Best Practices

1. **Token Storage:** Use `sessionStorage` instead of `localStorage` for admin tokens
2. **Automatic Logout:** Clear admin token when browser tab closes
3. **Warning Banner:** Show "Admin Mode" banner when in admin dashboard
4. **Separate Auth:** Don't mix admin and user authentication states
5. **Key Security:** Never log or expose admin private key in console/network

---

## Getting Admin Key

The admin private key is displayed **ONCE** when running:
```bash
python scripts/init_db.py
```

**Output:**
```
======================================================================
ADMIN PRIVATE KEY (SAVE THIS - IT WILL NOT BE SHOWN AGAIN!):
======================================================================

6cb85cd49b6fb4f02f849574337ffc5c4726f11822b32c31e0794a385a0cace8

======================================================================
```

**Important:** Save this key securely. It cannot be recovered if lost.

---

## Error Handling

### 401 Unauthorized
- Admin key is invalid
- Action: Redirect to admin login

### 403 Forbidden
- Valid token but not an admin
- Action: Show "Admin access required" error

### 404 Not Found
- Profile to unblock doesn't exist
- Action: Show error, refresh list

### 400 Bad Request
- Profile is not blocked (trying to unblock active user)
- Action: Show "User is not blocked" message
