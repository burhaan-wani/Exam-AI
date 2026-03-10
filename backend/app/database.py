from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()

client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.database_name]

users_collection = db["users"]
syllabus_collection = db["syllabus"]
final_question_paper_collection = db["final_question_paper"]
student_answers_collection = db["student_answers"]
evaluation_results_collection = db["evaluation_results"]
question_bank_collection = db["question_bank"]
documents_collection = db["documents"]


async def init_indexes():
    """Create database indexes on startup."""
    await users_collection.create_index("email", unique=True)
    await syllabus_collection.create_index("user_id")
    await final_question_paper_collection.create_index("syllabus_id")
    await student_answers_collection.create_index("paper_id")
    await evaluation_results_collection.create_index("answer_id")
    await evaluation_results_collection.create_index("paper_id")
    await question_bank_collection.create_index([("syllabus_id", 1), ("unit", 1), ("bloom_level", 1)])
    await documents_collection.create_index("syllabus_id")
