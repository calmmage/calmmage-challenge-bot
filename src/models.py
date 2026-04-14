from datetime import date, datetime, time
from typing import Literal, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

ProofPolicy = Literal["video_only", "text_or_video", "user_choice"]
UserProofChoice = Literal["video_only", "text_or_video"]
ProofKind = Literal["text", "video_note"]
SetupFlow = Literal["manual", "guided", "defaults"]
ChallengeStatus = Literal["draft", "active", "finished"]


class _BaseDoc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: Optional[ObjectId] = Field(default=None, alias="_id")


class Challenge(_BaseDoc):
    code: str
    name: str
    group_chat_id: Optional[int] = None
    created_by: int
    created_at: datetime
    starts_at: date
    ends_at: Optional[date] = None
    bed_proof_policy: ProofPolicy = "text_or_video"
    wake_proof_policy: ProofPolicy = "text_or_video"
    status: ChallengeStatus = "draft"
    allowed_registrants: Optional[list[int]] = None


class ChallengeUser(_BaseDoc):
    user_id: int
    challenge_id: ObjectId
    tz: str
    bedtime_deadline: time
    wakeup_deadline: time
    bed_proof_choice: Optional[UserProofChoice] = None
    wake_proof_choice: Optional[UserProofChoice] = None
    usual_bedtime: Optional[time] = None
    usual_wakeup: Optional[time] = None
    setup_flow: SetupFlow = "manual"
    joined_at: datetime
    active: bool = True


class CheckIn(BaseModel):
    ts: datetime
    kind: ProofKind
    on_time: bool


class SleepLog(_BaseDoc):
    user_id: int
    challenge_id: ObjectId
    date: date
    bed: Optional[CheckIn] = None
    wake: Optional[CheckIn] = None
    online_last_seen: Optional[datetime] = None
    score: float = 0.0
    streak_after: int = 0
    finalized: bool = False
