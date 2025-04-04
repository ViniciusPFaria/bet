from app import app, db, Participant
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_database():
    try:
        with app.app_context():
            # Get the count before deletion for reporting
            count = Participant.query.count()
            logger.info(f"Found {count} participants to delete")
            
            # Delete all participants
            Participant.query.delete()
            db.session.commit()
            
            # Verify deletion
            new_count = Participant.query.count()
            logger.info(f"Database cleared. {count} participants deleted. Remaining: {new_count}")
            
            return True, f"{count} participants deleted successfully"
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        db.session.rollback()
        return False, f"Error: {str(e)}"

if __name__ == "__main__":
    success, message = clear_database()
    print(message) 