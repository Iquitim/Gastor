
import sys
import os

# Add backend to path (parent directory)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from core import auth  # Import auth module for hashing
from core import models



def promote_user(email):
    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    
    # Get config from env
    default_password = os.getenv("ADMIN_PASSWORD", "admin")
    telegram_chat_id = os.getenv("ADMIN_TELEGRAM_CHAT_ID")

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            print(f"User {email} not found! Creating new admin user...")
            hashed_password = auth.hash_password(default_password)
            new_user = models.User(
                email=email,
                username=email.split("@")[0][:20], # Generate username from email
                hashed_password=hashed_password,
                role="admin",
                is_active=True,
                telegram_chat_id=telegram_chat_id
            )
            db.add(new_user)
            db.commit()
            print(f"User {email} created successfully with role ADMIN.")
            print(f"Password set from env.")
            if telegram_chat_id:
                print(f"Telegram Chat ID set to: {telegram_chat_id}")
            # user variable is None, so we set it to new_user for the next steps
            user = new_user
            needs_commit = True

        # User exists - promote and update optional fields if provided
        needs_commit = False
        
        if user.role != "admin":
            user.role = "admin"
            needs_commit = True
            print(f"User {email} promoted to ADMIN.")
        
        # Only update telegram config if it's the MAIN admin (first one roughly, or if specific logic needed)
        # For now, we update it if provided to ensure at least one admin gets alerts
        if telegram_chat_id and user.telegram_chat_id != telegram_chat_id:
            user.telegram_chat_id = telegram_chat_id
            needs_commit = True
            print(f"User {email} Telegram Chat ID updated to {telegram_chat_id}.")
            
        # ALWAYS Sync with TelegramConfig model (used by frontend)
        if telegram_chat_id:
            tg_config = db.query(models.TelegramConfig).filter(models.TelegramConfig.user_id == user.id).first()
            if not tg_config:
                print(f"Creating TelegramConfig for {email}")
                tg_config = models.TelegramConfig(
                    user_id=user.id,
                    chat_id=telegram_chat_id,
                    is_active=True
                )
                db.add(tg_config)
                needs_commit = True
            elif tg_config.chat_id != telegram_chat_id:
                print(f"Updating TelegramConfig for {email}")
                tg_config.chat_id = telegram_chat_id
                needs_commit = True
            
        if needs_commit:
            db.commit()
            print(f"User {email} updated successfully.")
        else:
             print(f"User {email} is already up to date.")

    except Exception as e:
        print(f"Error promoting {email}: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Read emails from env (comma separated)
    admin_emails_str = os.getenv("ADMIN_EMAILS", "")
    
    # Also support the hardcoded/default one if env is empty, but better to rely on env now
    if not admin_emails_str and len(sys.argv) > 1:
        admin_emails_str = sys.argv[1]
    
    if admin_emails_str:
        emails = [e.strip() for e in admin_emails_str.split(",") if e.strip()]
        print(f"Promoting {len(emails)} admins: {emails}")
        for email in emails:
            promote_user(email)
    else:
        print("No ADMIN_EMAILS found in env.")
