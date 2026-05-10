import os
from fastapi import APIRouter, HTTPException
from models import User, UserCreate, UserUpdate
from database import get_connection

router = APIRouter(prefix="/api/user", tags=["user"])

def _get_db_path():
    return os.environ.get("TEST_DB_PATH") or None

@router.post("", response_model=User)
def create_user(user_data: UserCreate):
    user = User(
        voice_preference=user_data.voice_preference,
        onboarding_mode=user_data.onboarding_mode
    )

    with get_connection(_get_db_path()) as conn:
        conn.execute(
            """INSERT INTO users (id, voice_preference, onboarding_mode)
               VALUES (?, ?, ?)""",
            (user.id, user.voice_preference, user.onboarding_mode)
        )
        conn.commit()

    return user

@router.get("/{user_id}", response_model=User)
def get_user(user_id: str):
    with get_connection(_get_db_path()) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    if not row:
        raise HTTPException(404, "User not found")

    return User(
        id=row["id"],
        created_at=row["created_at"],
        voice_preference=row["voice_preference"],
        onboarding_mode=row["onboarding_mode"],
        diagnostic_completed=bool(row["diagnostic_completed"])
    )

@router.put("/{user_id}", response_model=User)
def update_user(user_id: str, update: UserUpdate):
    with get_connection(_get_db_path()) as conn:
        # Check user exists
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if not row:
            raise HTTPException(404, "User not found")

        # Build update query
        updates = []
        values = []

        if update.voice_preference is not None:
            updates.append("voice_preference = ?")
            values.append(update.voice_preference)
        if update.onboarding_mode is not None:
            updates.append("onboarding_mode = ?")
            values.append(update.onboarding_mode)
        if update.diagnostic_completed is not None:
            updates.append("diagnostic_completed = ?")
            values.append(update.diagnostic_completed)

        if updates:
            values.append(user_id)
            conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()

        # Return updated user
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    return User(
        id=row["id"],
        created_at=row["created_at"],
        voice_preference=row["voice_preference"],
        onboarding_mode=row["onboarding_mode"],
        diagnostic_completed=bool(row["diagnostic_completed"])
    )
