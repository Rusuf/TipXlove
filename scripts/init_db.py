from app import create_app, db
from app.models.user import Creator
from app.models.transaction import Transaction
from app.models.withdrawal import Withdrawal

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Create a test creator if none exists
    if not Creator.query.first():
        test_creator = Creator(
            username='testcreator',
            email='test@example.com',
            tip_link_id='test123'
        )
        db.session.add(test_creator)
        db.session.commit()
        print("Created test creator account")
    
    print("Database initialized successfully")

if __name__ == "__main__":
    init_db() 