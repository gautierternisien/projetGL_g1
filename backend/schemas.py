from pydantic import BaseModel
from typing import List, Optional

# --- USER ---
class UserBase(BaseModel):
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserPublic(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class FriendActivity(BaseModel):
    friend_id: int
    friend_username: str
    mission_title: str
    mission_id: int
    status: str
    timestamp: Optional[str] = None

class FriendRequestSchema(BaseModel):
  id: int
  sender: UserPublic
  receiver: UserPublic
  status: str

  class Config:
    from_attributes = True

# --- APP ---

class OptionBase(BaseModel):
    label: str
    value: str
    score: int
    is_default: bool = False

class Option(OptionBase):
    id: int
    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    text: str

class Question(QuestionBase):
    id: int
    options: List[Option] = []
    class Config:
        from_attributes = True

class MissionBase(BaseModel):
    title: str
    description: Optional[str] = None

class Mission(MissionBase):
    id: int
    status: Optional[str] = "new" # Default for API response if not set
    class Config:
        from_attributes = True

class MissionUpdate(BaseModel):
    status: str

class UserAnswerBase(BaseModel):
    question_id: int
    answer_value: str

class UserAnswer(UserAnswerBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True
