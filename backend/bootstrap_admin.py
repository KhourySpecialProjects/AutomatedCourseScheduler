"""Insert yourself as the first real admin user.

Use this when you need to test the full invite flow end-to-end. The email
you provide must match the account you log in with via Auth0 — that's how
the backend links your auth0_sub on first login.

Usage (from backend/ directory):
python bootstrap_admin.py --nuid 12345678 --first-name Jane
--last-name Doe --email j.doe@northeastern.edu
"""

import argparse
import sys

from app.core.database import Base, SessionLocal, engine
from app.models.user import User


def bootstrap(nuid: int, first_name: str, last_name: str, email: str) -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        by_nuid = db.query(User).filter(User.nuid == nuid).first()
        if by_nuid:
            print(
                f"A user with NUID {nuid} already exists"\
                f"(role: {by_nuid.role}, email: {by_nuid.email})"
            )
            sys.exit(0)

        by_email = db.query(User).filter(User.email == email).first()
        if by_email:
            print(f"A user with email {email} already exists (NUID: {by_email.nuid})")
            sys.exit(0)

        user = User(
            nuid=nuid,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role="admin",
            auth0_sub=None,
            active=True,
        )
        db.add(user)
        db.commit()
        print(f"Admin created: {first_name} {last_name} <{email}> NUID={nuid}")
        print(
            "Next: log in via the frontend. Your auth0_sub will be linked automatically" \
            " on the first request to GET /api/users/me."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap the first real admin user.")
    parser.add_argument(
        "--nuid", type=int, required=True, help="Your Northeastern NUID"
    )
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument(
        "--email", required=True, help="Must match your Auth0 login email"
    )
    args = parser.parse_args()

    bootstrap(args.nuid, args.first_name, args.last_name, args.email)
