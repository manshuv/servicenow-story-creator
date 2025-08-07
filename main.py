#!/usr/bin/env python3
import argparse
import os
import sys
import re
import json
import urllib.parse
from typing import Tuple, Optional

import requests
from dotenv import load_dotenv
# import markdown as md  # used only if --html-description


def parse_markdown(file_path: str) -> Tuple[str, str, Optional[str]]:
    """
    Parse markdown to extract:
    - title (from first H1 or first non-empty line), with leading 'User Story:' removed
    - description (prefer content under '**Description:**' if present; otherwise rest of doc)
    - acceptance_criteria (content under '**Acceptance Criteria:**' if present)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError("Markdown file is empty.")

    lines = content.splitlines()

    title: Optional[str] = None
    title_line_idx: Optional[int] = None

    for idx, line in enumerate(lines):
        # Match H1: "# Something" (allow leading spaces)
        if re.match(r"^\s*#\s+.+", line):
            title = re.sub(r"^\s*#\s+", "", line).strip()
            title_line_idx = idx
            break

    if title is None:
        # fallback: first non-empty line
        for idx, line in enumerate(lines):
            if line.strip():
                title = line.strip()
                title_line_idx = idx
                break

    if title is None:
        raise ValueError("Could not determine a title from the markdown.")

    # Sanitize title: remove leading 'User Story:' (case-insensitive) if present
    title = re.sub(r"^\s*user\s*story:\s*", "", title, flags=re.IGNORECASE).strip()

    # Build a simple section parser for bold headers like '**Description:**' and '**Acceptance Criteria:**'
    section_headers_pattern = re.compile(r"^\s*\*\*([^*]+):\*\*\s*$", re.IGNORECASE)
    sections: dict[str, list[str]] = {}
    current_section: Optional[str] = None

    # Start scanning from after the title line (if we found one)
    scan_start = (title_line_idx + 1) if title_line_idx is not None else 0
    for line in lines[scan_start:]:
        m = section_headers_pattern.match(line)
        if m:
            current_section = m.group(1).strip()
            sections[current_section] = []
            continue
        if current_section is not None:
            sections[current_section].append(line)

    # Prefer explicit Description section if present
    description_section = None
    for key in sections.keys():
        if key.lower() == "description":
            description_section = "\n".join(sections[key]).strip()
            break

    # Extract Acceptance Criteria if present
    acceptance_criteria = None
    for key in sections.keys():
        if key.lower() == "acceptance criteria":
            acceptance_criteria = "\n".join(sections[key]).strip()
            break

    if description_section is not None:
        description = description_section
    else:
        # Fallback: Description is the rest of the doc after the title line
        desc_lines = lines[scan_start:]
        # If we detected an Acceptance Criteria section, remove it from the fallback description
        if acceptance_criteria:
            acc_start_idx = None
            for i, l in enumerate(desc_lines):
                if re.match(r"^\s*\*\*Acceptance Criteria:\*\*\s*$", l, re.IGNORECASE):
                    acc_start_idx = i
                    break
            if acc_start_idx is not None:
                desc_lines = desc_lines[:acc_start_idx]
        description = "\n".join(desc_lines).strip()

    return title, description, acceptance_criteria


def build_headers() -> dict:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def get_instance_base_url(raw_url: str) -> str:
    """
    Normalize instance URL.
    Accepts full UI URLs like https://instance.service-now.com/now/nav/ui/home
    and returns https://instance.service-now.com
    """
    raw_url = raw_url.strip()
    if not raw_url:
        raise ValueError("SN_INSTANCE is empty.")

    # Parse and rebuild scheme://netloc
    parsed = urllib.parse.urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        # If user gave only instance host, prepend https
        if "." in raw_url:
            return f"https://{raw_url}"
        raise ValueError("SN_INSTANCE must be a full URL like https://yourinstance.service-now.com")

    return f"{parsed.scheme}://{parsed.netloc}"


def api_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def ensure_credentials():
    load_dotenv()
    instance = os.getenv("SN_INSTANCE", "").strip()
    username = os.getenv("SN_USERNAME", "").strip()
    password = os.getenv("SN_PASSWORD", "").strip()

    if not instance or not username or not password:
        raise EnvironmentError(
            "Missing credentials. Set SN_INSTANCE, SN_USERNAME, and SN_PASSWORD "
            "via environment variables or a .env file."
        )

    return get_instance_base_url(instance), username, password


def find_existing_story(session: requests.Session, base_url: str, title: str) -> Optional[dict]:
    """
    Find a story with exact short_description match.
    Returns the first result dict or None.
    """
    # Encode query for exact match on short_description
    query = f"short_description={title}"
    params = {
        "sysparm_query": query,
        "sysparm_limit": "1",
    }
    url = api_url(base_url, "/api/now/table/rm_story")
    resp = session.get(url, headers=build_headers(), params=params)
    if not resp.ok:
        raise RuntimeError(f"Failed to search stories: {resp.status_code} {resp.text}")
    data = resp.json()
    result = data.get("result", [])
    if isinstance(result, list) and result:
        return result[0]
    # Try legacy title prefixed with 'User Story:' to match previously created items
    legacy = f"User Story: {title}"
    params_legacy = {
        "sysparm_query": f"short_description={legacy}",
        "sysparm_limit": "1",
    }
    resp2 = session.get(url, headers=build_headers(), params=params_legacy)
    if not resp2.ok:
        return None
    data2 = resp2.json()
    result2 = data2.get("result", [])
    if isinstance(result2, list) and result2:
        return result2[0]
    return None


def create_story(session: requests.Session, base_url: str, payload: dict) -> dict:
    url = api_url(base_url, "/api/now/table/rm_story")
    resp = session.post(url, headers=build_headers(), data=json.dumps(payload))
    if not resp.ok:
        raise RuntimeError(f"Create failed: {resp.status_code} {resp.text}")
    return resp.json().get("result", {})


def update_story(session: requests.Session, base_url: str, sys_id: str, payload: dict) -> dict:
    url = api_url(base_url, f"/api/now/table/rm_story/{sys_id}")
    resp = session.patch(url, headers=build_headers(), data=json.dumps(payload))
    if not resp.ok:
        raise RuntimeError(f"Update failed: {resp.status_code} {resp.text}")
    return resp.json().get("result", {})


def make_story_url(base_url: str, sys_id: str) -> str:
    # Direct record URL
    return f"{base_url}/nav_to.do?uri=rm_story.do?sys_id={sys_id}"


def main():
    parser = argparse.ArgumentParser(description="Publish a Markdown user story to ServiceNow rm_story")
    parser.add_argument("--file", required=True, help="Path to the markdown file")
    parser.add_argument(
        "--update-if-exists",
        action="store_true",
        help="If a story with the same short_description exists, update it instead of creating a new one",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Send plain text (disable Markdown to HTML conversion)",
    )
    # Add optional fields as needed
    parser.add_argument("--priority", help="Set priority (e.g., 1, 2, 3, 4, 5)")
    parser.add_argument("--assigned-to", dest="assigned_to", help="Assigned to (user sys_id)")
    parser.add_argument("--product", help="Product (sys_id)")
    parser.add_argument("--story-points", dest="story_points", help="Story points (integer)")
    parser.add_argument("--additional", help="Additional JSON to merge into payload (e.g. '{\"u_custom\":\"val\"}')")

    args = parser.parse_args()

    md_path = os.path.expanduser(args.file)
    if not os.path.isfile(md_path):
        print(f"File not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    title, description, acceptance_criteria = parse_markdown(md_path)

    # Default: convert Markdown to HTML unless --plain is specified
    if not args.plain:
        try:
            import markdown as md
        except ImportError:
            print("Missing 'markdown' package. Install it or run with --plain.", file=sys.stderr)
            sys.exit(1)
        description = md.markdown(description)
        if acceptance_criteria is not None and acceptance_criteria.strip():
            acceptance_criteria = md.markdown(acceptance_criteria)

    base_url, username, password = ensure_credentials()

    # Prepare payload
    payload = {
        "short_description": title[:160],  # ServiceNow often truncates; keep it concise
        "description": description,
        # Add any defaults you want here
    }
    if acceptance_criteria:
        payload["acceptance_criteria"] = acceptance_criteria

    # Optional fields
    if args.priority:
        payload["priority"] = args.priority
    if args.assigned_to:
        payload["assigned_to"] = args.assigned_to
    if args.product:
        payload["product"] = args.product
    if args.story_points:
        payload["story_points"] = args.story_points

    if args.additional:
        try:
            extra = json.loads(args.additional)
            if isinstance(extra, dict):
                payload.update(extra)
            else:
                raise ValueError("Additional payload must be a JSON object")
        except Exception as e:
            print(f"Invalid --additional JSON: {e}", file=sys.stderr)
            sys.exit(1)

    with requests.Session() as session:
        session.auth = (username, password)

        existing = find_existing_story(session, base_url, title)
        if existing and args.update_if_exists:
            sys_id = existing.get("sys_id")
            updated = update_story(session, base_url, sys_id, payload)
            url = make_story_url(base_url, updated.get("sys_id", sys_id))
            print("Updated existing story:")
            print(json.dumps(updated, indent=2))
            print(f"URL: {url}")
        elif existing and not args.update_if_exists:
            url = make_story_url(base_url, existing.get("sys_id"))
            print("A story with the same short_description already exists.")
            print(json.dumps(existing, indent=2))
            print(f"URL: {url}")
            print("Re-run with --update-if-exists to update it, or edit your title.")
            sys.exit(0)
        else:
            created = create_story(session, base_url, payload)
            url = make_story_url(base_url, created.get("sys_id"))
            print("Created new story:")
            print(json.dumps(created, indent=2))
            print(f"URL: {url}")


if __name__ == "__main__":
    main()
