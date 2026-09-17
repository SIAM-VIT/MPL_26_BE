"""Pydantic request/response models.

Split into one module per domain so every file stays small; this package
re-exports everything, so existing imports such as
``from app.schemas import TeamLogin, SubmissionOut`` keep working unchanged.
"""
from app.schemas.questions import (
    QuestionBase,
    QuestionCreate,
    QuestionResponse,
    TestCaseBase,
    TestCaseCreate,
    TestCaseAdmin,
    TestCasePublic,
    MainQuestionPublic,
    QuestionSetBase,
    QuestionSetCreate,
    QuestionSetResponse,
    QuestionSetDetail,
)
from app.schemas.teams import (
    TeamBase,
    TeamCreate,
    TeamLogin,
    TeamStatusResponse,
    ChallengeCreate,
    AssignBoost,
    ReviewMarkSolved,
    AddTimeRequest,
    AssignRandomBoostRequest,
    VerifyBoostRequest,
    VerifyMainQuestionRequest,
    CancelBoostRequest,
    AssignBiddingRequest,
)
from app.schemas.submissions import (
    CodeSubmitRequest,
    TestResultOut,
    SubmissionOut,
)
from app.schemas.admin import (
    LeaderboardRow,
    RejudgeResponse,
)

__all__ = [
    "QuestionBase", "QuestionCreate", "QuestionResponse",
    "TestCaseBase", "TestCaseCreate", "TestCaseAdmin", "TestCasePublic",
    "MainQuestionPublic",
    "QuestionSetBase", "QuestionSetCreate", "QuestionSetResponse", "QuestionSetDetail",
    "TeamBase", "TeamCreate", "TeamLogin", "TeamStatusResponse",
    "ChallengeCreate", "AssignBoost", "AssignBiddingRequest", "ReviewMarkSolved", "AddTimeRequest",
    "AssignRandomBoostRequest", "VerifyBoostRequest", "VerifyMainQuestionRequest", "CancelBoostRequest",
    "CodeSubmitRequest", "TestResultOut", "SubmissionOut",
    "LeaderboardRow", "RejudgeResponse",
]


