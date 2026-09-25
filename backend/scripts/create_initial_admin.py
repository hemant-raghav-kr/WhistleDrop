"""Safe Administrator Account Provisioning Script for WhistleDrop.

Creates or updates the primary system administrator account on the database:
- Never hardcodes passwords
- Accepts password via environment variable (ADMIN_PASSWORD), argument (--password), or interactive getpass prompt
- Never prints passwords or password hashes to logs or stdout
- Employs standard bcrypt 12 rounds hashing
- Guarantees role = UserRole.ADMIN and is_active = True
"""

import argparse
import getpass
import logging
import os
import sys

# Ensure backend root is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.moderator import Moderator, UserRole

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("whistledrop.init_admin")


def create_or_update_admin(
    db: Session,
    email: str,
    username: str,
    name: str,
    password: str,
) -> Moderator:
    """Safely provision or update the administrator account."""
    if len(password) < 8:
        raise ValueError("Admin password must be at least 8 characters long.")

    clean_email = email.lower().strip()
    clean_username = username.strip()

    admin = (
        db.query(Moderator)
        .filter(
            or_(
                Moderator.email == clean_email,
                Moderator.username == clean_username,
                Moderator.role == UserRole.ADMIN,
            )
        )
        .first()
    )

    hashed_pw = get_password_hash(password)

    if admin:
        admin.email = clean_email
        admin.username = clean_username
        admin.name = name.strip() if name else "System Administrator"
        admin.hashed_password = hashed_pw
        admin.role = UserRole.ADMIN
        admin.is_active = True
        logger.info(f"Existing account updated to primary ADMIN: '{clean_username}' ({clean_email})")
    else:
        admin = Moderator(
            name=name.strip() if name else "System Administrator",
            email=clean_email,
            username=clean_username,
            hashed_password=hashed_pw,
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        logger.info(f"Created new primary ADMIN account: '{clean_username}' ({clean_email})")

    db.commit()
    db.refresh(admin)
    return admin


def main():
    parser = argparse.ArgumentParser(description="WhistleDrop Initial Administrator Setup")
    parser.add_argument(
        "--email",
        default=os.environ.get("ADMIN_EMAIL", "admin@whistledrop.org"),
        help="Administrator email address (default: admin@whistledrop.org or ADMIN_EMAIL env var)",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("ADMIN_USERNAME", "admin"),
        help="Administrator username (default: admin or ADMIN_USERNAME env var)",
    )
    parser.add_argument(
        "--name",
        default="System Administrator",
        help="Administrator display name",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("ADMIN_PASSWORD"),
        help="Administrator password (or supply via ADMIN_PASSWORD env var / interactive prompt)",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Optional database connection URL override (defaults to settings.DATABASE_URL)",
    )

    args = parser.parse_args()

    password = args.password
    if not password:
        # Prompt interactively if not provided via CLI or environment
        if sys.stdin.isatty():
            password = getpass.getpass("Enter Initial Admin Password (min 8 chars): ")
            confirm = getpass.getpass("Confirm Admin Password: ")
            if password != confirm:
                logger.error("Passwords do not match. Aborting.")
                sys.exit(1)
        else:
            logger.error("Admin password not provided. Supply via ADMIN_PASSWORD environment variable or --password.")
            sys.exit(1)

    if len(password) < 8:
        logger.error("Admin password must be at least 8 characters long.")
        sys.exit(1)

    db_url = args.database_url or settings.DATABASE_URL
    standard_url = settings.assemble_database_url(db_url)

    engine = create_engine(standard_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()

    try:
        create_or_update_admin(
            db=db,
            email=args.email,
            username=args.username,
            name=args.name,
            password=password,
        )
        logger.info("Administrator provisioning completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to provision administrator: {e}")
        sys.exit(1)
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()
