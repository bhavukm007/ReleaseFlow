from datetime import date, timedelta

from app.database.session import SessionLocal
from app.models.release import Release
from app.models.user import User
from app.core.security import hash_password
from app.schemas.release import default_steps


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(Release).count():
            print("Seed skipped: releases already exist.")
            return
        user = db.query(User).filter(User.email == "demo@releaseflow.local").one_or_none()
        if user is None:
            user = User(full_name="Demo User", email="demo@releaseflow.local", hashed_password=hash_password("DemoPassword123!"))
            db.add(user)
            db.flush()
        today = date.today()
        planned = default_steps()
        ongoing = default_steps()
        for name in list(ongoing)[:3]:
            ongoing[name] = True
        done = {name: True for name in default_steps()}
        db.add_all(
            [
                Release(owner_id=user.id, name="Mobile App 2.0", due_date=today + timedelta(days=7), additional_info="Coordinate app store review.", steps=planned),
                Release(owner_id=user.id, name="Payments Refresh", due_date=today + timedelta(days=14), additional_info="Monitor checkout metrics after rollout.", steps=ongoing),
                Release(owner_id=user.id, name="Infrastructure Upgrade", due_date=today - timedelta(days=2), additional_info="Successfully deployed.", steps=done),
            ]
        )
        db.commit()
        print("Created 3 sample releases.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
