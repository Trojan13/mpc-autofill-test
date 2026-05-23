"""Background indexer for syncing Google Drive sources."""

from datetime import datetime, timezone

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Image, ImageSource, SourceType
from app.services.google_drive import (
    get_drive_service,
    get_service_account_drive_service,
    list_drive_images,
    list_drive_folders,
)


async def sync_google_drive_source(source: ImageSource, db: AsyncSession) -> None:
    """
    Sync a Google Drive source: list all images in the configured folder
    and update the Image table.
    """
    if source.source_type != SourceType.GOOGLE_DRIVE:
        return

    folder_id = source.config.get("folder_id")
    if not folder_id:
        return

    # Determine which service to use
    if source.user_id:
        # Personal drive — use user's refresh token
        from app.models import User

        result = await db.exec(select(User).where(User.id == source.user_id))
        user = result.first()
        if not user or not user.google_refresh_token:
            return
        service = get_drive_service(user.google_refresh_token)
    else:
        # Community drive — use service account
        service = get_service_account_drive_service()
        if service is None:
            return

    # Recursively index all images
    await _index_folder(service=service, folder_id=folder_id, source=source, db=db)

    # Update last synced time
    source.last_synced_at = datetime.now(timezone.utc)
    await db.commit()


async def _index_folder(service, folder_id: str, source: ImageSource, db: AsyncSession) -> None:
    """Recursively index images from a Drive folder."""
    # Get images in this folder
    images = list_drive_images(service, folder_id)

    for img_data in images:
        file_id = img_data["id"]
        name = img_data["name"]

        # Check if image already exists
        result = await db.exec(
            select(Image).where(Image.external_id == file_id, Image.source_id == source.id)
        )
        existing = result.first()

        height = img_data.get("imageMediaMetadata", {}).get("height")
        file_size = int(img_data.get("size", 0))
        thumbnail_url = f"https://drive.google.com/thumbnail?sz=w400-h400&id={file_id}"
        full_url = f"https://drive.google.com/thumbnail?sz=w800-h800&id={file_id}"

        if existing:
            # Update existing
            existing.name = _clean_image_name(name)
            existing.thumbnail_url = thumbnail_url
            existing.full_url = full_url
            existing.height = height
            existing.file_size = file_size
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            image = Image(
                name=_clean_image_name(name),
                source_id=source.id,
                external_id=file_id,
                thumbnail_url=thumbnail_url,
                full_url=full_url,
                height=height,
                file_size=file_size,
            )
            db.add(image)

    await db.commit()

    # Recurse into subfolders
    subfolders = list_drive_folders(service, folder_id)
    for folder in subfolders:
        await _index_folder(service=service, folder_id=folder["id"], source=source, db=db)


def _clean_image_name(filename: str) -> str:
    """Remove file extension from image name."""
    if "." in filename:
        return filename.rsplit(".", 1)[0]
    return filename
