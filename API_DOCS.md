# Authentication API Documentation

## Login

Authenticate a user and get an access token.

**Base URL:** `https://orangebackend.palman.app`
**Endpoint:** `/api/auth/login`
**Method:** `POST`
**Authentication Required:** No

### Request Body

```json
{
    "email": "user@example.com",
    "password": "yourpassword"
}
```

### Response

#### Success Response (200 OK)
```json
{
    "success": true,
    "user": {
        "id": 1,
        "email": "user@example.com"
    },
    "token": "your_access_token_here"
}
```

#### Error Response (400 Bad Request)
```json
{
    "success": false,
    "message": "Invalid credentials"
}
```

### Example Usage

```bash
curl -X POST https://orangebackend.palman.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword"
  }'
```

### Notes
- The returned token should be included in subsequent authenticated requests in the Authorization header
- Format: `Authorization: Bearer <token>`
- Tokens do not expire and are valid until the user logs in again (which generates a new token) 