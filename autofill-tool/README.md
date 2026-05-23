# MPC Autofill Tool

A Playwright-based automation tool that reads a project JSON export from the MPC Autofill web app and automates filling in card images on the MPC (makeplayingcards.com) website.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

1. Export your project from the MPC Autofill web app (Projects → Export JSON)
2. Run the autofill tool:

```bash
python autofill.py my-project.json
```

### Options

- `--headless` — Run the browser without a visible window (useful for automation)

## Project JSON Format

The tool expects a JSON file with this structure:

```json
{
  "project_name": "My Cards",
  "slots": [
    {
      "slot_number": 1,
      "face": "front",
      "image_url": "https://...",
      "image_name": "Card Name"
    },
    {
      "slot_number": 1,
      "face": "back",
      "image_url": "https://...",
      "image_name": "Card Back"
    }
  ]
}
```

## How It Works

1. Opens a Chromium browser and navigates to MPC
2. Waits for you to log in and set up your order (product type, quantity)
3. Automatically uploads images to each card slot (fronts first, then backs)
4. Lets you review the order before closing
