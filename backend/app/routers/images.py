"""Images router — upload, browse, and search images."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.deps import get_db, get_current_user, require_user
from app.models import (
    CardType,
    Image,
    ImageRead,
    ImageSearch,
    ImageSource,
    SourceType,
    User,
)
from app.services.storage import upload_file

router = APIRouter()


@router.post("/search", response_model=list[ImageRead])
async def search_images(
    body: ImageSearch,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> list[ImageRead]:
    """
    Search images across all accessible sources.
    Community sources are always visible. Personal sources require authentication.
    """
    query = select(Image).join(ImageSource)

    # Text search on name
    if body.query:
        query = query.where(Image.name.ilike(f"%{body.query}%"))  # type: ignore[union-attr]

    # Filter by card type
    if body.card_type:
        query = query.where(Image.card_type == body.card_type)

    # Filter by source
    if body.source_id:
        query = query.where(Image.source_id == body.source_id)

    # Only show images from community sources or the user's own sources
    if user:
        query = query.where(
            (ImageSource.user_id == None) | (ImageSource.user_id == user.id)  # noqa: E711
        )
    else:
        query = query.where(ImageSource.user_id == None)  # noqa: E711

    # Pagination
    offset = (body.page - 1) * body.per_page
    query = query.offset(offset).limit(body.per_page)

    result = await db.exec(query)
    images = result.all()
    return [ImageRead.model_validate(img) for img in images]


@router.post("/upload", response_model=ImageRead)
async def upload_image(
    file: UploadFile = File(...),
    name: str = Form(...),
    card_type: CardType = Form(CardType.CARD),
    tags: str = Form(""),  # comma-separated
    source_id: UUID = Form(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ImageRead:
    """
    Upload an image to an upload-type source.
    The image is stored in S3 and metadata is saved to the database.
    """
    # Verify the source belongs to the user and is an upload type
    result = await db.exec(
        select(ImageSource).where(
            ImageSource.id == source_id,
            ImageSource.user_id == user.id,
            ImageSource.source_type == SourceType.UPLOAD,
        )
    )
    source = result.first()
    if source is None:
        raise HTTPException(status_code=404, detail="Upload source not found")

    if file.content_type not in ("image/png", "image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only PNG and JPEG images are supported")

    # Upload to S3
    content = await file.read()
    file_url, thumbnail_url = await upload_file(
        content=content,
        filename=file.filename or "image.png",
        content_type=file.content_type or "image/png",
        user_id=str(user.id),
    )

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Create image record
    image = Image(
        name=name,
        card_type=card_type,
        tags=tag_list,
        source_id=source_id,
        full_url=file_url,
        thumbnail_url=thumbnail_url,
        file_size=len(content),
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return ImageRead.model_validate(image)


@router.get("/{image_id}", response_model=ImageRead)
async def get_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ImageRead:
    """Get a single image by ID."""
    result = await db.exec(select(Image).where(Image.id == image_id))
    image = result.first()
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return ImageRead.model_validate(image)


@router.delete("/{image_id}")
async def delete_image(
    image_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Delete an image (must belong to the user)."""
    result = await db.exec(
        select(Image).join(ImageSource).where(Image.id == image_id, ImageSource.user_id == user.id)
    )
    image = result.first()
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    await db.delete(image)
    await db.commit()
    return {"status": "deleted"}
