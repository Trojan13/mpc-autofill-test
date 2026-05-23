"""Google Drive service — OAuth flow and API access."""

from uuid import UUID

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.models import ImageSource, SourceType, User

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _create_flow() -> Flow:
    """Create a Google OAuth flow for Drive access."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri.replace("/login", "/google-drive/callback"),
    )


def start_drive_oauth(user_id: str) -> str:
    """
    Generate a Google OAuth URL for the user to grant Drive access.
    The user_id is passed as state so we can associate the token later.
    """
    flow = _create_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=user_id,
        prompt="consent",
    )
    return auth_url


async def handle_drive_oauth_callback(code: str, state: str, db: AsyncSession) -> None:
    """
    Handle the OAuth callback. Exchange the code for tokens and save them.
    The state parameter contains the user_id.
    """
    flow = _create_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials

    user_id = UUID(state)
    result = await db.exec(select(User).where(User.id == user_id))
    user = result.first()
    if user is None:
        raise ValueError("User not found")

    # Store refresh token
    user.google_refresh_token = credentials.refresh_token
    await db.commit()


def get_drive_service(refresh_token: str):
    """Create a Google Drive API service using a user's refresh token."""
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )
    return build("drive", "v3", credentials=credentials)


def get_service_account_drive_service():
    """Create a Google Drive API service using the service account (for community drives)."""
    from google.oauth2 import service_account

    if not settings.google_service_account_key_path:
        return None

    credentials = service_account.Credentials.from_service_account_file(
        settings.google_service_account_key_path,
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    return build("drive", "v3", credentials=credentials)


def list_drive_folders(service, folder_id: str) -> list[dict]:
    """List subfolders in a Google Drive folder."""
    results = (
        service.files()
        .list(
            q=f"mimeType='application/vnd.google-apps.folder' and '{folder_id}' in parents and trashed=false",
            fields="files(id, name)",
            pageSize=100,
        )
        .execute()
    )
    return results.get("files", [])


def list_drive_images(service, folder_id: str) -> list[dict]:
    """List image files in a Google Drive folder."""
    all_images = []
    page_token = None

    while True:
        results = (
            service.files()
            .list(
                q=(
                    f"(mimeType='image/png' or mimeType='image/jpeg') "
                    f"and '{folder_id}' in parents and trashed=false"
                ),
                fields="nextPageToken, files(id, name, size, imageMediaMetadata, createdTime, modifiedTime)",
                pageSize=500,
                pageToken=page_token,
            )
            .execute()
        )
        all_images.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return all_images
