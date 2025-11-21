import asyncio
import pkgutil
import importlib
from database import engine, Base

# --------------------------
# Dynamically import all models in "models" package
# --------------------------
def import_all_models(package_name: str):
    """Recursively import all modules in a package to register tables in Base.metadata."""
    package = importlib.import_module(package_name)

    # Only if package has __path__ (i.e., it’s a folder/package)
    if hasattr(package, "__path__"):
        for _, modname, ispkg in pkgutil.iter_modules(package.__path__):
            full_name = f"{package_name}.{modname}"
            importlib.import_module(full_name)
            if ispkg:
                import_all_models(full_name)  # recursive import for subpackages

# --------------------------
# Flush DB function
# --------------------------
async def flush_db():
    # Import models dynamically
    import_all_models("models")  # change "models" if your models are in a different folder

    confirm = input("⚠️ Are you sure you want to flush the database? This will DELETE ALL DATA! (yes/no): ")
    if confirm.lower() != "yes":
        print("Operation cancelled.")
        return

    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables fresh...")
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database flushed successfully.")

# --------------------------
# Run standalone
# --------------------------
if __name__ == "__main__":
    asyncio.run(flush_db())
