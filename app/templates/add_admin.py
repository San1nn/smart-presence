import sys
import getpass
from sqlalchemy.orm import Session

# Add the project's root directory to the Python path
# This allows the script to import modules from the 'app' package
sys.path.append('.')

from app.database.connection import SessionLocal
from app.models.attendance import Admin, User # Import both User and the specific Admin model
from app.services.auth_service import get_password_hash

def add_admin():
    """
    A command-line utility to securely add a new administrator to the database.
    """
    print("--- Create New Administrator Account ---")
    
    # Establish a connection to the database
    db: Session = SessionLocal()
    
    try:
        # --- 1. Get User Input ---
        name = input("Enter admin's full name: ").strip()
        email = input("Enter admin's email address: ").strip().lower()

        if not name or not email:
            print("\n❌ Error: Name and email cannot be empty.")
            return

        # Use getpass for secure, hidden password entry
        password = getpass.getpass("Enter a secure password for the admin: ")
        confirm_password = getpass.getpass("Confirm the password: ")

        if not password:
            print("\n❌ Error: Password cannot be empty.")
            return

        if password != confirm_password:
            print("\n❌ Error: Passwords do not match.")
            return

        # --- 2. Check if a user with that email already exists ---
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"\n❌ Error: A user with the email '{email}' already exists in the system.")
            return

        # --- 3. Hash the Password ---
        hashed_password = get_password_hash(password)
        print("\nPassword successfully hashed.")

        # --- 4. Create and Save the New Admin ---
        print("Creating new admin record...")
        
        # By creating an 'Admin' object, SQLAlchemy's polymorphic identity
        # automatically sets the 'role' column to 'admin'.
        new_admin = Admin(
            name=name,
            email=email,
            hashed_password=hashed_password
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin) # Refresh to get the auto-generated userID

        print("\n" + "="*40)
        print("✅ SUCCESS: Administrator added to the database!")
        print(f"   User ID: {new_admin.userID}")
        print(f"   Name:    {new_admin.name}")
        print(f"   Email:   {new_admin.email}")
        print("="*40)

    except Exception as e:
        db.rollback() # Roll back any changes if an error occurs
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        db.close() # Always close the database session

if __name__ == "__main__":
    add_admin()