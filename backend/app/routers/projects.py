"""Projects router — manage card projects and export for autofill."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.deps import get_db, require_user
from app.models import (
    Image,
    Project,
    ProjectCreate,
    ProjectExport,
    ProjectExportSlot,
    ProjectRead,
    ProjectSlot,
    ProjectSlotCreate,
    ProjectSlotRead,
    User,
)

router = APIRouter()


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectRead]:
    """List all projects for the authenticated user."""
    result = await db.exec(select(Project).where(Project.user_id == user.id))
    projects = result.all()
    return [ProjectRead.model_validate(p) for p in projects]


@router.post("/", response_model=ProjectRead)
async def create_project(
    body: ProjectCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Create a new project."""
    project = Project(name=body.name, user_id=user.id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Get a single project."""
    result = await db.exec(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Delete a project."""
    result = await db.exec(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return {"status": "deleted"}


# --- Slots ---


@router.get("/{project_id}/slots", response_model=list[ProjectSlotRead])
async def list_slots(
    project_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectSlotRead]:
    """List all slots in a project."""
    # Verify ownership
    result = await db.exec(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    if result.first() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.exec(
        select(ProjectSlot).where(ProjectSlot.project_id == project_id)
    )
    slots = result.all()
    return [ProjectSlotRead.model_validate(s) for s in slots]


@router.post("/{project_id}/slots", response_model=ProjectSlotRead)
async def create_slot(
    project_id: UUID,
    body: ProjectSlotCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectSlotRead:
    """Add a slot to a project."""
    result = await db.exec(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    if result.first() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    slot = ProjectSlot(
        project_id=project_id,
        slot_number=body.slot_number,
        face=body.face,
        image_id=body.image_id,
    )
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return ProjectSlotRead.model_validate(slot)


@router.delete("/{project_id}/slots/{slot_id}")
async def delete_slot(
    project_id: UUID,
    slot_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Remove a slot from a project."""
    result = await db.exec(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    if result.first() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.exec(
        select(ProjectSlot).where(ProjectSlot.id == slot_id, ProjectSlot.project_id == project_id)
    )
    slot = result.first()
    if slot is None:
        raise HTTPException(status_code=404, detail="Slot not found")

    await db.delete(slot)
    await db.commit()
    return {"status": "deleted"}


# --- Export ---


@router.get("/{project_id}/export", response_model=ProjectExport)
async def export_project(
    project_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectExport:
    """
    Export a project as a JSON structure for the autofill tool.
    Contains all slot assignments with image URLs.
    """
    result = await db.exec(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.exec(
        select(ProjectSlot).where(ProjectSlot.project_id == project_id)
    )
    slots = result.all()

    export_slots: list[ProjectExportSlot] = []
    for slot in slots:
        image_url = None
        image_name = None
        if slot.image_id:
            img_result = await db.exec(select(Image).where(Image.id == slot.image_id))
            image = img_result.first()
            if image:
                image_url = image.full_url
                image_name = image.name

        export_slots.append(
            ProjectExportSlot(
                slot_number=slot.slot_number,
                face=slot.face,
                image_url=image_url,
                image_name=image_name,
            )
        )

    return ProjectExport(project_name=project.name, slots=export_slots)
