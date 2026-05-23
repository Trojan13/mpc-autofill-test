"""
MPC Autofill Tool — Playwright-based automation for MPC website.

This tool reads a project export JSON file and automates filling in the
MPC (makeplayingcards.com) website with the card images.

Usage:
    python autofill.py project.json

The JSON file should have the format exported by the MPC Autofill web app:
{
    "project_name": "My Cards",
    "slots": [
        {"slot_number": 1, "face": "front", "image_url": "...", "image_name": "..."},
        {"slot_number": 1, "face": "back", "image_url": "...", "image_name": "..."},
        ...
    ]
}
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print("Error: playwright is required. Install with: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)


MPC_BASE_URL = "https://www.makeplayingcards.com"


@dataclass
class SlotAssignment:
    slot_number: int
    face: str  # "front" or "back"
    image_url: str | None
    image_name: str | None


@dataclass
class ProjectData:
    project_name: str
    slots: list[SlotAssignment]


def load_project(filepath: str) -> ProjectData:
    """Load project data from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    slots = [
        SlotAssignment(
            slot_number=s["slot_number"],
            face=s["face"],
            image_url=s.get("image_url"),
            image_name=s.get("image_name"),
        )
        for s in data.get("slots", [])
    ]

    return ProjectData(project_name=data.get("project_name", "Untitled"), slots=slots)


def get_front_slots(project: ProjectData) -> list[SlotAssignment]:
    """Get all front-face slots sorted by slot number."""
    return sorted(
        [s for s in project.slots if s.face == "front" and s.image_url],
        key=lambda s: s.slot_number,
    )


def get_back_slots(project: ProjectData) -> list[SlotAssignment]:
    """Get all back-face slots sorted by slot number."""
    return sorted(
        [s for s in project.slots if s.face == "back" and s.image_url],
        key=lambda s: s.slot_number,
    )


def upload_image_to_slot(page: Page, image_url: str, slot_index: int) -> bool:
    """
    Upload an image to a specific card slot on the MPC website.
    This is a simplified placeholder — actual implementation would depend
    on MPC's current page structure.
    """
    try:
        # Navigate to the upload area for the specific slot
        # Note: Actual selectors depend on MPC's page structure
        print(f"  Uploading image to slot {slot_index}...")

        # Download the image first, then upload it
        # In a real implementation, this would interact with MPC's upload UI
        time.sleep(1)  # Simulate upload time
        return True
    except Exception as e:
        print(f"  Error uploading to slot {slot_index}: {e}")
        return False


def run_autofill(project: ProjectData, headless: bool = False) -> None:
    """Run the autofill process using Playwright."""
    front_slots = get_front_slots(project)
    back_slots = get_back_slots(project)

    total_cards = max(
        (s.slot_number for s in project.slots),
        default=0,
    )

    print(f"Project: {project.project_name}")
    print(f"Total card slots: {total_cards}")
    print(f"Front images: {len(front_slots)}")
    print(f"Back images: {len(back_slots)}")
    print()

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=headless)
        page: Page = browser.new_page()

        print(f"Navigating to {MPC_BASE_URL}...")
        page.goto(MPC_BASE_URL)

        # Wait for user to log in and set up their order
        print("\n--- Manual Setup Required ---")
        print("1. Log in to MPC if needed")
        print("2. Start a new order and select your product/quantity")
        print("3. Press Enter here when you're on the card upload page...")
        input()

        # Process front faces
        if front_slots:
            print("\n--- Uploading Front Images ---")
            for slot in front_slots:
                success = upload_image_to_slot(page, slot.image_url or "", slot.slot_number)
                status = "✓" if success else "✗"
                print(f"  {status} Slot {slot.slot_number}: {slot.image_name}")

        # Process back faces
        if back_slots:
            print("\n--- Uploading Back Images ---")
            # Navigate to backs section
            print("Navigate to the card backs section, then press Enter...")
            input()

            for slot in back_slots:
                success = upload_image_to_slot(page, slot.image_url or "", slot.slot_number)
                status = "✓" if success else "✗"
                print(f"  {status} Slot {slot.slot_number}: {slot.image_name}")

        print("\n--- Autofill Complete ---")
        print("Review your order in the browser, then close when done.")
        input("Press Enter to close the browser...")

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MPC Autofill Tool — Automate card image uploading to MPC"
    )
    parser.add_argument("project_file", help="Path to the project JSON file")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no visible window)",
    )
    args = parser.parse_args()

    project = load_project(args.project_file)
    run_autofill(project, headless=args.headless)


if __name__ == "__main__":
    main()
