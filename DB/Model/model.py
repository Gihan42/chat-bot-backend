from DB.db_config import get_db
from passlib.context import CryptContext



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_collection():
    db = get_db()
    collection = db['user']
    return collection

def hash_password(password: str) -> str:
    hashed = pwd_context.hash(password)
    print(f"Hashed password: {hashed}")  
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    print(f"Verifying password: {plain_password} against {hashed_password}")  
    return pwd_context.verify(plain_password, hashed_password)



def insert_document(document):
    collection = create_collection()
    document['password'] = hash_password(document['password'])
    collection.insert_one(document)

def find_user_by_email(email: str):
    collection = create_collection()
    user = collection.find_one({"email": email})
    print(f"User found: {user}")
    return user


def find_documents(query):
    collection = create_collection()
    return list(collection.find(query))

def update_password(email: str, new_password: str) -> bool:
    collection = create_collection()
    hashed_password = hash_password(new_password)  # Hash the new password
    result = collection.update_one({"email": email}, {"$set": {"password": hashed_password}})
    return result.modified_count > 0