"""SQLModel database models for MPC Autofill."""

import enum
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class CardType(str, enum.Enum):
    CARD = "card"
    CARDBACK = "cardback"
    TOKEN = "token"


class SourceType(str, enum.Enum):
    GOOGLE_DRIVE = "google_drive"
    UPLOAD = "upload"


class Face(str, enum.Enum):
    FRONT = "front"
    BACK = "back"


# --- User ---


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    name: str
    avatar_url: Optional[str] = None


class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    google_refresh_token: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    sources: list["ImageSource"] = Relationship(back_populates="owner")
    projects: list["Project"] = Relationship(back_populates="owner")


class UserRead(UserBase):
    id: UUID
    created_at: datetime


# --- Image Source ---


class ImageSourceBase(SQLModel):
    name: str
    source_type: SourceType
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))


class ImageSource(ImageSourceBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_synced_at: Optional[datetime] = None

    owner: Optional[User] = Relationship(back_populates="sources")
    images: list["Image"] = Relationship(back_populates="source")


class ImageSourceCreate(SQLModel):
    name: str
    source_type: SourceType
    config: dict = Field(default_factory=dict)


class ImageSourceRead(ImageSourceBase):
    id: UUID
    user_id: Optional[UUID]
    created_at: datetime
    last_synced_at: Optional[datetime]


# --- Image ---


class ImageBase(SQLModel):
    name: str
    card_type: CardType = CardType.CARD
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    thumbnail_url: Optional[str] = None
    full_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None


class Image(ImageBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_id: UUID = Field(foreign_key="imagesource.id")
    external_id: Optional[str] = None  # e.g. Google Drive file ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    source: ImageSource = Relationship(back_populates="images")


class ImageRead(ImageBase):
    id: UUID
    source_id: UUID
    created_at: datetime
    updated_at: datetime


class ImageSearch(SQLModel):
    query: str = ""
    card_type: Optional[CardType] = None
    source_id: Optional[UUID] = None
    tags: list[str] = Field(default_factory=list)
    page: int = 1
    per_page: int = 50


# --- Project ---


class ProjectBase(SQLModel):
    name: str


class Project(ProjectBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    owner: User = Relationship(back_populates="projects")
    slots: list["ProjectSlot"] = Relationship(back_populates="project")


class ProjectCreate(SQLModel):
    name: str


class ProjectRead(ProjectBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


# --- Project Slot ---


class ProjectSlotBase(SQLModel):
    slot_number: int
    face: Face


class ProjectSlot(ProjectSlotBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="project.id")
    image_id: Optional[UUID] = Field(default=None, foreign_key="image.id")

    project: Project = Relationship(back_populates="slots")
    image: Optional[Image] = Relationship()


class ProjectSlotCreate(SQLModel):
    slot_number: int
    face: Face
    image_id: Optional[UUID] = None


class ProjectSlotRead(ProjectSlotBase):
    id: UUID
    project_id: UUID
    image_id: Optional[UUID]


# --- Project Export (for autofill tool) ---


class ProjectExportSlot(SQLModel):
    slot_number: int
    face: Face
    image_url: Optional[str] = None
    image_name: Optional[str] = None


class ProjectExport(SQLModel):
    project_name: str
    slots: list[ProjectExportSlot]
