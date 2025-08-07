# ServiceNow Markdown Story Publisher

Publish a local Markdown user story to ServiceNow `rm_story` via the Table API.

## Setup
1. Create a virtual environment and install dependencies:
   - `python3 -m venv .venv`
   - `.venv/bin/python -m pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your credentials:
   - `SN_INSTANCE=https://empmverma1.service-now.com`
   - `SN_USERNAME=your_username`
   - `SN_PASSWORD=your_password`

Note: If you paste a UI URL ending with `/now/nav/ui/home`, the script will normalize it to the base instance URL automatically.

## Usage
```
.venv/bin/python main.py --file "/Users/manshu.verma/Library/CloudStorage/OneDrive-ServiceNow/Written Word/SDLC Stories/story_lock_fields_in_dev.md"
```

Options:
- `--update-if-exists` Update a story that has the same `short_description` instead of creating a duplicate.
- `--plain` Send plain text instead of converting Markdown to HTML (HTML is the default).
- `--priority 1..5` Set priority field.
- `--assigned-to <sys_id>` Assign to a user by sys_id.
- `--product <sys_id>` Set product by sys_id.
- `--story-points <int>` Set story points.
- `--additional '{"u_custom":"value"}'` Merge arbitrary fields into the payload.

## How it works
- Title extraction: first H1 (`# Title`) becomes `short_description`. If no H1, the first non-empty line is used.
- Description: remainder of the markdown file is converted to HTML by default (use `--plain` to disable conversion).
- Idempotency: The script searches for an exact `short_description` match and updates it when `--update-if-exists` is used.

## Permissions
Ensure your ServiceNow user has permission to create/update `rm_story` via the Table API and that your instance allows basic auth or your chosen auth method.
