from sqlalchemy.orm import Session

from app.models.user import User


def get_by_auth0_sub(db: Session, sub: str) -> User | None:
    return db.query(User).filter(User.auth0_sub == sub).first()


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_by_nuid(db: Session, nuid: int) -> User | None:
    return db.query(User).filter(User.nuid == nuid).first()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.user_id == user_id).first()


def get_all(db: Session) -> list[User]:
    return db.query(User).order_by(User.last_name, User.first_name).all()


def create(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_auth0_sub(db: Session, user: User, sub: str) -> User:
    user.auth0_sub = sub
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
