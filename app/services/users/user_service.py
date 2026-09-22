# /app/services/users/user_service.py | Updated: 2026-05-06 11:30 AM

from sqlalchemy.orm import Session
from app.models.company.user import User
from app.schemas.users.user_schema import UserCreate, UserUpdate


class UserService:

    # ---------------------------------------------------
    # CREATE USER
    # ---------------------------------------------------
    def create_user(self, db: Session, user_data: UserCreate):
        new_user = User(
            full_name=user_data.full_name,
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            role=user_data.role,
            address=user_data.address,
            city=user_data.city,
            state=user_data.state,
            postal_code=user_data.postal_code,
            country=user_data.country,
            location=user_data.location,
            phone_1=user_data.phone_1,
            phone_2=user_data.phone_2,
            is_active=user_data.is_active,
            position=user_data.position,
            salary=user_data.salary,
            hire_date=user_data.hire_date,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    # ---------------------------------------------------
    # GET USER BY ID
    # ---------------------------------------------------
    def get_user_by_id(self, db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    # ---------------------------------------------------
    # GET USER BY USERNAME
    # ---------------------------------------------------
    def get_user_by_username(self, db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    # ---------------------------------------------------
    # GET ALL USERS
    # ---------------------------------------------------
    def get_all_users(self, db: Session):
        return db.query(User).all()

    # ---------------------------------------------------
    # UPDATE USER
    # ---------------------------------------------------
    def update_user(self, db: Session, user_id: int, user_data: UserUpdate):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        update_data = user_data.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    # ---------------------------------------------------
    # DELETE USER
    # ---------------------------------------------------
    def delete_user(self, db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        db.delete(user)
        db.commit()
        return True

    # ---------------------------------------------------
    # PAGINATION + FILTERS
    # ---------------------------------------------------
    def get_users_paginated(
        self,
        db: Session,
        page: int = 1,
        limit: int = 10,
        search: str = "",
        role: str = "",
        active: str = ""
    ):
        query = db.query(User)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(search_term)) |
                (User.username.ilike(search_term)) |
                (User.email.ilike(search_term))
            )

        if role:
            query = query.filter(User.role == role)

        if active == "true":
            query = query.filter(User.is_active == True)
        elif active == "false":
            query = query.filter(User.is_active == False)

        total_records = query.count()
        total_pages = (total_records + limit - 1) // limit

        offset = (page - 1) * limit
        users = query.offset(offset).limit(limit).all()

        return users, total_pages


# ---------------------------------------------------
# INSTANCE TO IMPORT
# ---------------------------------------------------
user_service = UserService()
