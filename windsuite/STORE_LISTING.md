# ServiceNow Story Publisher

Short description
Publish Markdown user stories from Windsurf directly to ServiceNow rm_story — with HTML formatting, idempotent updates, and field mapping.

Overview
ServiceNow Story Publisher lets you publish the active Markdown file as a story into the rm_story table. It parses your document to extract:
- Title (H1 or first non-empty line) → short_description (removes leading "User Story:" if present)
- Description → description (HTML by default)
- **Acceptance Criteria:** → acceptance_criteria (HTML by default)

If a story with the same short_description exists, the plugin updates it (configurable). Great for SDLC teams who keep specs in Markdown and want a one-click publish to ServiceNow.

Key features
- One-click publish from active Markdown file
- HTML by default for rich Description and Acceptance Criteria (Markdown supported)
- Idempotent: update existing story by short_description
- Instance URL normalization (accepts full UI URLs)
- Secure secrets for credentials

Permissions required
- network: to call ServiceNow Table API
- filesystem: to read the active Markdown file (provided by Windsurf host)

Settings
- sn_instance (string, required): e.g., https://yourinstance.service-now.com
- auth_method (select): basic (currently supported)
- send_as_html (boolean, default true): convert Markdown to HTML for description and acceptance_criteria

Secrets
- sn_username
- sn_password (hidden)

Usage
1) Open a Markdown story in Windsurf.
2) Run command: "Publish Story to ServiceNow" (publish_story_from_markdown), or use the context menu.
3) The plugin reads settings/secrets, parses your file, and creates/updates rm_story.
4) A success message includes a direct link to the record.

Markdown structure expected
- # Title (H1) or first non-empty line
- **Description:** (optional). If omitted, the body after the title is used.
- **Acceptance Criteria:** (optional) — lines or lists; converted to HTML automatically.
- Any leading "User Story:" in the title is stripped.

Troubleshooting
- 401/403: Ensure your user has permission to create/update rm_story via the Table API and that basic auth is allowed.
- Invalid instance URL: Ensure a valid https URL like https://yourinstance.service-now.com (UI paths are normalized).
- Not updating: Confirm the short_description matches your Title exactly; enable updateIfExists (default true).

Privacy & security
- Credentials are stored as encrypted plugin secrets.
- The plugin only sends required fields to the ServiceNow instance you configure.
- No analytics/telemetry.

Support
- Report issues: https://github.com/manshuv/servicenow-story-creator/issues
- License: MIT

Changelog
- 0.1.0: Initial release (HTML by default, Description + Acceptance Criteria mapping, idempotent updates)

Screenshots / media
- Settings panel: assets/screenshots/screenshot-settings.svg
- Command palette: assets/screenshots/screenshot-command.svg
- Publishing flow (GIF placeholder): assets/screenshots/publish-flow.svg

Tip: Replace the SVG placeholders with actual PNGs/GIF recorded from your environment before store submission.
