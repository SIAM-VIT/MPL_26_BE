from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class QuestionSet(Base):
    """A bundle of 3 questions (1 Debug, 1 Math, 1 Leetcode) with allocation status."""
    __tablename__ = "question_sets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)  # e.g., "Set A", "Set 1"

    debug_question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    math_question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    leetcode_question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)

    is_allocated = Column(Boolean, default=False, index=True)
    allocated_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, unique=True)
    allocated_at = Column(DateTime, nullable=True)

    debug_question = relationship("Question", foreign_keys=[debug_question_id], lazy="selectin")
    math_question = relationship("Question", foreign_keys=[math_question_id], lazy="selectin")
    leetcode_question = relationship("Question", foreign_keys=[leetcode_question_id], lazy="selectin")
    allocated_team = relationship("Team", back_populates="question_set", lazy="selectin")

    @property
    def questions(self):
        """Return list of non-null questions in this set."""
        return [q for q in (self.debug_question, self.math_question, self.leetcode_question) if q is not None]

