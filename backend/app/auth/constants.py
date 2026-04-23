from fastapi import HTTPException, status

JWT_ALGORITHM = "HS256"
JWT_LEEWAY = 30.0
UNAUTHORIZED_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized."
)
FORBIDDEN_EXCEPTION = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
