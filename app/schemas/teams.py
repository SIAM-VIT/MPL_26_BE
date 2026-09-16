"""Pydantic models for teams, login, and the legacy challenge/boost flows."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    passcode: str


class TeamLogin(BaseModel):
    name: str
    passcode: str


class TeamStatusResponse(BaseModel):
    id: int
    name: str
    points: int
    timer_start_time: Optional[datetime]
    extra_time_seconds: int
    main_question_id: Optional[int]
    session_token: Optional[str] = None   # returned on login only
    model_config = ConfigDict(from_attributes=True)


class ChallengeCreate(BaseModel):
    question_id: int
    team1_id: int
    team2_id: int
    team3_id: Optional[int] = None


class AssignBoost(BaseModel):
    question_id: int


class ReviewMarkSolved(BaseModel):
    team_id: int
    question_id: int


class AddTimeRequest(BaseModel):
    seconds: int


class AssignRandomBoostRequest(BaseModel):
    difficulty: Optional[str] = "MEDIUM"


class VerifyBoostRequest(BaseModel):
    question_id: int
    passcode: str


class CancelBoostRequest(BaseModel):
    question_id: int


class VerifyChallengeSubmitRequest(BaseModel):
    session_id: int
    passcode: str


class ResolveChallengeRequest(BaseModel):
    winner_team_id: int

