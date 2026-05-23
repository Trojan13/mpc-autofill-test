"""Sources router — manage image sources (Google Drive, uploads)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.deps import get_db, get_current_user, require_user
from app.models import (
    ImageSource,
    ImageSourceCreate,
    ImageSourceRead,
    SourceType,
    User,
)
from app.services.google_drive import start_drive_oauth, handle_drive_oauth_callback
from app.services.indexer import sync_google_drive_source

router = APIRouter()


@router.get("/", response_model=list[ImageSourceRead])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> list[ImageSourceRead]:
    """
    List all accessible image sources.
    Community sources (user_id=None) are always visible.
    Personal sources are only visible to their owner.
    """
    query = select(ImageSource)
    if user:
        query = query.where(
            (ImageSource.user_id == None) | (ImageSource.user_id == user.id)  # noqa: E711
        )
    else:
        query = query.where(ImageSource.user_id == None)  # noqa: E711

    result = await db.exec(query)
    sources = result.all()
    return [ImageSourceRead.model_validate(s) for s in sources]


@router.post("/", response_model=ImageSourceRead)
async def create_source(
    body: ImageSourceCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ImageSourceRead:
    """Create a new image source for the authenticated user."""
    source = ImageSource(
        name=body.name,
        source_type=body.source_type,
        config=body.config,
        user_id=user.id,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return ImageSourceRead.model_validate(source)


@router.delete("/{source_id}")
async def delete_source(
    source_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Delete a source (must belong to the user)."""
    result = await db.exec(
        select(ImageSource).where(ImageSource.id == source_id, ImageSource.user_id == user.id)
    )
    source = result.first()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{source_id}/sync")
async def sync_source(
    source_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Trigger a sync for a Google Drive source."""
    result = await db.exec(
        select(ImageSource).where(ImageSource.id == source_id, ImageSource.user_id == user.id)
    )
    source = result.first()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    if source.source_type != SourceType.GOOGLE_DRIVE:
        raise HTTPException(status_code=400, detail="Only Google Drive sources can be synced")

    await sync_google_drive_source(source=source, db=db)
    return {"status": "sync_started"}


@router.get("/google-drive/connect")
async def connect_google_drive(
    user: User = Depends(require_user),
) -> dict[str, str]:
    """Get the Google OAuth URL to connect a personal Google Drive."""
    url = start_drive_oauth(user_id=str(user.id))
    return {"oauth_url": url}


@router.get("/google-drive/callback")
async def google_drive_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Handle the Google OAuth callback after user grants Drive access."""
    await handle_drive_oauth_callback(code=code, state=state, db=db)
    return {"status": "connected"}
