import asyncio
from getpass import getpass
from database import async_session, Base, engine
from models import Admin
from auth import hash_password

async def create_admin():
    async with async_session() as session:
        # Input ID manually
        admin_id = input("Enter admin ID : ")

        # Prompt for password securely
        password = getpass("Enter new admin password: ")
        confirm_password = getpass("Confirm password: ")

        if password != confirm_password:
            print("❌ Passwords do not match.")
            return

        # Check if ID already exists
        existing = await session.get(Admin, admin_id)
        if existing:
            print(f"❌ Admin with ID {admin_id} already exists.")
            return

        # Hash the password using Argon2
        hashed_password = hash_password(password)

        # Create Admin record with manual ID
        new_admin = Admin(user_id=admin_id, password_hash=hashed_password)
        session.add(new_admin)
        await session.commit()
        await session.refresh(new_admin)

        print(f"✅ Admin created with ID: {new_admin.user_id}")

# --------------------------
# Run standalone
# --------------------------
if __name__ == "__main__":
    async def main():
        # Ensure tables exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create admin
        await create_admin()

    asyncio.run(main())
