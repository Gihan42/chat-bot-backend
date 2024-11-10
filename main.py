from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from huggingface_hub import InferenceClient
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, ValidationError
from DB.Model.model import find_user_by_email,update_password ,verify_password, insert_document, hash_password, create_collection
import os
from fastapi import Body


app = FastAPI()



# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "absrefgh")  # Replace with a secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdatePasswordRequest(BaseModel):
    email: str
    current_password: str
    new_password: str

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"Encoded JWT: {encoded_jwt}")  
    return encoded_jwt


@app.post("/token",response_model=UserResponse)
def login_for_access_token(request: LoginRequest):
    user = find_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer","user":user}

@app.post("/users", response_model=UserResponse)
def create_user(user: User):
    print(user)
    
 
    existing_user = find_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
  
    hashed_password = hash_password(user.password)
    user_dict = user.dict()
   
    
   
    insert_document(user_dict)

   
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

   
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.put("/update")
def update_user(email: str = Body(...), name: str = Body(...)):
    
    user = find_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    
    collection = create_collection()
    result = collection.update_one({"email": email}, {"$set": {"name": name}})
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )

    return {"email": email, "name": name, "message": "User updated successfully"}

    

@app.get("/users", response_model=List[User])
def get_all_users():
    collection = create_collection()
    users = list(collection.find({}))

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    try:
        user_list = [User(**user) for user in users]
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=f"Data validation error: {e}")

    return user_list

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = find_user_by_email(email)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user


@app.put("/update-password")
def update_password_endpoint(request: UpdatePasswordRequest):
    user = find_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(request.current_password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Call update_password correctly with email and new password
    if update_password(request.email, request.new_password):  # Correct call
        return {"detail": "Password updated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )














# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize Hugging Face client
client = InferenceClient(
    api_key="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"
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    response: str
    messages: List[Message]

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    try:
        # Convert Pydantic messages to dict format for HuggingFace
        messages = [{"role": msg.role, "content": msg.content} for msg in chat_request.messages]
        
        # Create the completion request
        stream = client.chat.completions.create(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=messages,
            max_tokens=500,
            stream=True
        )
        
        # Accumulate the response
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        
        # Update messages with assistant's response
        messages.append({"role": "assistant", "content": full_response})
        
        return ChatResponse(
            response=full_response,
            messages=[Message(**msg) for msg in messages]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



