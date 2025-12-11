from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'unbound_gateway')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Collections
users_collection = db['users']
rules_collection = db['rules']
commands_collection = db['command_executions']

async def init_db():
    """Initialize database with indexes and seed data"""
    
    # Create indexes
    await users_collection.create_index('api_key', unique=True)
    await users_collection.create_index('user_id', unique=True)
    await rules_collection.create_index('id', unique=True)
    await rules_collection.create_index('order')
    await commands_collection.create_index('user_id')
    await commands_collection.create_index('timestamp')
    
    # Seed initial admin user if not exists
    admin_exists = await users_collection.find_one({'role': 'admin'})
    if not admin_exists:
        admin_user = {
            'user_id': 'admin_001',
            'api_key': 'admin_key_123',
            'name': 'Admin User',
            'role': 'admin',
            'credits': 100,
            'created_at': None
        }
        await users_collection.insert_one(admin_user)
        print("✓ Admin user seeded: admin_key_123")
    
    # Seed initial member users
    member1_exists = await users_collection.find_one({'user_id': 'member_001'})
    if not member1_exists:
        member1 = {
            'user_id': 'member_001',
            'api_key': 'member_key_456',
            'name': 'John Doe',
            'role': 'member',
            'credits': 10,
            'created_at': None
        }
        await users_collection.insert_one(member1)
        print("✓ Member user seeded: member_key_456")
    
    member2_exists = await users_collection.find_one({'user_id': 'member_002'})
    if not member2_exists:
        member2 = {
            'user_id': 'member_002',
            'api_key': 'member_key_789',
            'name': 'Jane Smith',
            'role': 'member',
            'credits': 8,
            'created_at': None
        }
        await users_collection.insert_one(member2)
        print("✓ Member user seeded: member_key_789")
    
    # Seed initial rules
    rules_count = await rules_collection.count_documents({})
    if rules_count == 0:
        initial_rules = [
            {
                'id': 'rule_001',
                'pattern': r'^git (pull|fetch|status)',
                'action': 'AUTO_ACCEPT',
                'description': 'Safe git read operations',
                'order': 1,
                'created_at': '2024-07-15T10:30:00Z'
            },
            {
                'id': 'rule_002',
                'pattern': r'^rm -rf',
                'action': 'AUTO_REJECT',
                'description': 'Dangerous file deletion',
                'order': 2,
                'created_at': '2024-07-15T10:31:00Z'
            },
            {
                'id': 'rule_003',
                'pattern': r'^sudo',
                'action': 'AUTO_REJECT',
                'description': 'Elevated privileges',
                'order': 3,
                'created_at': '2024-07-15T10:32:00Z'
            },
            {
                'id': 'rule_004',
                'pattern': r'^ls|^pwd|^echo',
                'action': 'AUTO_ACCEPT',
                'description': 'Basic shell commands',
                'order': 4,
                'created_at': '2024-07-15T10:33:00Z'
            }
        ]
        await rules_collection.insert_many(initial_rules)
        print(f"✓ Seeded {len(initial_rules)} initial rules")

async def get_db():
    return db
