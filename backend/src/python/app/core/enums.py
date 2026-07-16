from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class SubjectCategory(str, Enum):
    GENERAL = "GENERAL"
    PROGRAMMING = "PROGRAMMING"
    SCIENCE = "SCIENCE"
    LANGUAGE = "LANGUAGE"
    MEDICAL = "MEDICAL"

class PublishStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ARCHIVED = "archived"

class MemoryType(str, Enum):
    ACADEMIC = "ACADEMIC"
    BEHAVIOUR = "BEHAVIOUR"
    PREFERENCE = "PREFERENCE"
    PROFILE = "PROFILE"
    GOAL = "GOAL"

class VoiceStyle(str, Enum):
    WARM = "warm"
    FOCUSED = "focused"
    COMFORT = "comfort"
    QUIZ = "quiz"
    STORY = "story"
