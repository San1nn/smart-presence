import getpass
import sys

# Add the project root to the path to allow imports from 'app'
sys.path.append('.')

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.attendance import Admin, User
from app.services.auth_service import get_password_hash

def add_admin():
    """
    Command-line script to add a new admin to the database.
    """
    print("--- Add New Administrator ---")
    
    db: Session = SessionLocal()
    
    try:
        name = input("Enter admin's full name: ").strip()
        email = input("Enter admin's email address: ").strip().lower()
        
        if not name or not email:
            print("\n❌ Error: Name and email cannot be empty.")
            return

        password = getpass.getpass("Enter a password for the admin: ")
        confirm_password = getpass.getpass("Confirm the password: ")

        if not password:
            print("\n❌ Error: Password cannot be empty.")
            return

        if password != confirm_password:
            print("\n❌ Error: Passwords do not match.")
            return

        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"\n❌ Error: A user with the email '{email}' already exists.")
            return

        hashed_password = get_password_hash(password)
        
        # The 'role' is automatically set to 'admin' due to polymorphic identity
        new_admin = Admin(
            name=name,
            email=email,
            hashed_password=hashed_password
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        print("\n" + "="*40)
        print("✅ SUCCESS: Admin added to the database!")
        print(f"   ID: {new_admin.userID}")
        print(f"   Name: {new_admin.name}")
        print(f"   Email: {new_admin.email}")
        print("="*40)

    except Exception as e:
        db.rollback()
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_admin()