# ServiceNow Story Publisher (Windsurf Plugin)

Publish the active Markdown file as a ServiceNow rm_story directly from Windsurf.

## Settings
- sn_instance (required): e.g., https://yourinstance.service-now.com
- auth_method: currently supports "basic"
- send_as_html: convert Markdown to HTML (default: true)

Secrets
- sn_username
- sn_password (hidden)

## Command
- Publish Story to ServiceNow (publish_story_from_markdown)
  - Inputs: filePath (auto: active document path), updateIfExists (default: true)

## Behavior
- Title: H1 (or first non-empty line) becomes short_description (prefix "User Story:" removed if present)
- Description: Description section or remainder after title
- Acceptance Criteria: parsed from **Acceptance Criteria:** and sent to acceptance_criteria
- HTML: description and acceptance_criteria sent as HTML by default
- Idempotent: searches by short_description; updates if found and updateIfExists is true

## Development
- Node deps: axios, markdown-it
- Entry: windsuite/index.js
- Manifest: windsuite/plugin.json
