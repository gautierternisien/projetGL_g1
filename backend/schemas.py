from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

# --- USER ---
class UserBase(BaseModel):
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    xp:Optional[int] = 0

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    profile_image: Optional[str] = None
    xp: int = 0

    @property
    def level(self) -> int:
        return 1 + (self.xp // 100)

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
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True

class FriendProfile(BaseModel):
    id: int
    username: str
    mission_count: int
    trophy_count: int
    level: int
    xp: int
    profile_image: Optional[str] = None

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
    category_name: str
    conditions: Optional[List[str]] = []
    mission_type: Optional[str] = "one_shot"

class Mission(MissionBase):
    id: int
    status: Optional[str] = "new" # Default for API response if not set
    class Config:
        from_attributes = True

class MissionUpdate(BaseModel):
    status: str
    user_id: Optional[int] = None

class UserAnswerBase(BaseModel):
    question_id: int
    answer_value: str

class UserAnswer(UserAnswerBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True


class NgcStatsPayload(BaseModel):
    global_score: int
    details_by_category: Dict[str, float] = {}
    category_progress: Dict[str, float] = {}

# --- LEAGUE ---
class LeagueBase(BaseModel):
    name: str
    start_date: str
    end_date: str

class LeagueCreate(LeagueBase):
    pass

class League(LeagueBase):
    id: int
    is_archived: bool
    created_at: datetime
    members_count: int = 0

    class Config:
        from_attributes = True

class LeagueMember(BaseModel):
    id: int
    user_id: int
    username: str
    joined_at: datetime
    missions_completed: Optional[int] = 0 # Computed for ranking

    class Config:
        from_attributes = True

class LeagueInvite(BaseModel):
    id: int
    league_id: int
    league_name: str
    inviter_id: int
    inviter_name: str
    invitee_id: int
    status: str

    class Config:
        from_attributes = True

class LeagueDetail(League):
    members: List[LeagueMember] = []

class UserNgcAnswersCreate(BaseModel):
    data: Dict[str, Any]

class UserNgcAnswersResponse(UserNgcAnswersCreate):
    updated_at: Optional[str] = None
    class Config:
        from_attributes = True

class UserPreferenceBase(BaseModel):
    data: Dict[str, bool]
    has_completed_onboarding: bool

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreferenceResponse(UserPreferenceBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
# --- TROPHY ---
class TrophyBase(BaseModel):
    name: str
    title: str
    description: str
    icon: str
    tier: str  # bronze, silver, gold
    requirement_type: str
    requirement_value: int

class Trophy(TrophyBase):
    id: int
    class Config:
        from_attributes = True

class UserTrophyBase(BaseModel):
    trophy_id: int

class UserTrophy(UserTrophyBase):
    id: int
    user_id: int
    obtained_at: Optional[str] = None
    last_milestone_date: Optional[str] = None
    progress: int = 0
    is_obtained: bool = False
    trophy: Optional[Trophy] = None

    class Config:
        from_attributes = True
