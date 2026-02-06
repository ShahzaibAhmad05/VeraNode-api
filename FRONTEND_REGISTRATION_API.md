# Frontend Registration API - Updated Flow

## Registration Endpoint Changes

### POST `/auth/register`

**Updated Request Body:**
```json
{
  "email": "student@nust.edu.pk",
  "password": "securePassword123",
  "department": "SEECS"
}
```

**Field Requirements:**
- `email` (required): Must end with `.edu.pk`, contain `@` and `.` - validated at backend
- `password` (required): Minimum 8 characters
- `department` (required): User's department/area - Must be one of: `SEECS`, `NBS`, `ASAB`, `SINES`, `SCME`, `S3H`
  - **Important:** `General` is NOT a valid option for department selection

**Success Response (201):**
```json
{
  "success": true,
  "message": "Registration successful. SAVE YOUR SECRET KEY - it cannot be recovered or regenerated!",
  "secretKey": "a1b2c3d4e5f6...",
  "profile": {
    "area": "SEECS",
    "points": 100,
    "isBlocked": false,
    "createdAt": "2026-02-07T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 INVALID_EMAIL`: Email format invalid or doesn't end with .edu.pk
- `400 INVALID_PASSWORD`: Password less than 8 characters
- `400 INVALID_DEPARTMENT`: Invalid department or "General" was selected
- `409 EMAIL_EXISTS`: Email already registered

## Key Changes Summary

1. **Registration now requires 3 fields** instead of 1:
   - Email (`.edu.pk` validated)
   - Password
   - Department (area) - dropdown with: SEECS, NBS, ASAB, SINES, SCME, S3H

2. **Remove "General" from department dropdown** - it's only used for rumor voting areas, not user registration

3. **Secret key is still returned** upon registration - user must save it (cannot be recovered)

4. **Login remains unchanged** - still uses secret key only

## Department/Area Notes

- **User's department** determines their voting weight
- **Rumor's area of vote** can be any department OR "General"
- **When rumor area = "General"**: All votes have equal weightage regardless of voter's department
- **When rumor area = specific department**: Votes from that department have higher weight
