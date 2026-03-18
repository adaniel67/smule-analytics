# =============================================================================
# smule_analytics/api.py
#
# This module handles all communication with the Smule website.
# It sends HTTP requests (like your browser does) and receives JSON data back.
#
# KEY PYTHON CONCEPTS IN THIS FILE:
#   - Functions (def)
#   - Dictionaries (key: value pairs)
#   - f-strings (f"text {variable}")
#   - try/except (error handling)
#   - return values
#   - importing libraries
# =============================================================================

import re        # Standard library for text pattern matching ("regular expressions")
import requests  # Third-party library for making HTTP requests

# ---------------------------------------------------------------------------
# CONSTANTS
# These are values that stay the same throughout the program.
# ALL_CAPS naming is a Python convention for constants.
# ---------------------------------------------------------------------------
BASE_URL = "https://www.smule.com"

# Headers tell the Smule server that we look like a regular web browser.
# Without this, the server might reject our request.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.smule.com/",
}


# ---------------------------------------------------------------------------
# FUNCTION: get_user_profile_from_page
#
# Smule doesn't have a public JSON endpoint for profile data, so we fetch
# the user's HTML profile page and use a "regular expression" (regex) to
# pull out the data we need.
#
# A regular expression is a pattern for finding text — like a very powerful
# "find in page" tool. The re.search() function scans text for a pattern.
# ---------------------------------------------------------------------------
def get_user_profile_from_page(username: str) -> dict:
    """
    Scrape the Smule profile page to extract user info.

    Args:
        username: The Smule handle (e.g. "cacophonoussound")

    Returns:
        A dictionary with whatever profile fields we can find.
    """
    url = f"{BASE_URL}/{username}"
    html_headers = {**HEADERS, "Accept": "text/html"}  # ** "unpacks" a dict — merges two dicts

    try:
        response = requests.get(url, headers=html_headers, timeout=10)
        response.raise_for_status()
        html = response.text  # The raw HTML text of the page

        # Helper function to safely extract a number from an HTML pattern.
        # re.search(pattern, text) returns a Match object (or None if not found).
        # group(1) gets the text captured by the first set of parentheses in the pattern.
        def extract_int(pattern: str) -> int:
            match = re.search(pattern, html)
            return int(match.group(1)) if match else 0

        def extract_str(pattern: str) -> str:
            match = re.search(pattern, html)
            return match.group(1) if match else ""

        return {
            "handle": extract_str(r'"handle"\s*:\s*"([^"]+)"') or username,
            "name": extract_str(r'"name"\s*:\s*"([^"]+)"'),
            "follower_count": extract_int(r'"followersCount"\s*:\s*(\d+)'),
            "following_count": extract_int(r'"followingsCount"\s*:\s*(\d+)'),
            "num_performances": extract_int(r'"numPerformances"\s*:\s*(\d+)'),
            "location": extract_str(r'"location"\s*:\s*"([^"]+)"'),
            "is_verified": '"isVerified":true' in html,
        }

    except requests.exceptions.RequestException as e:
        print(f"[API] Could not fetch profile page: {e}")
        return {"handle": username}


# ---------------------------------------------------------------------------
# FUNCTION: get_performances
# ---------------------------------------------------------------------------
def get_performances(username: str, next_offset: int = 0) -> dict | None:
    """
    Fetch one page of performances for a user.

    The Smule API returns 25 performances at a time. Each response includes
    a `next_offset` value that tells us where to start for the next page.

    Args:
        username:    Smule handle
        next_offset: Where to start (0 = first page, 25 = second page, etc.)

    Returns:
        A dict with "list" (performances) and "next_offset", or None on error.
    """
    # This is the working Smule endpoint discovered by testing
    url = f"{BASE_URL}/s/profile/performance/{username}"

    # Query parameters are added to the URL: ?next_offset=0
    params = {"next_offset": next_offset}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"[API] HTTP error fetching performances: {e}")
        return None
    except requests.exceptions.RequestException as e:
        # RequestException is the base class for all requests errors
        print(f"[API] Error: {e}")
        return None


# ---------------------------------------------------------------------------
# FUNCTION: get_all_performances
# ---------------------------------------------------------------------------
def get_all_performances(username: str, max_pages: int = 10) -> list:
    """
    Fetch performances, deduplicating by performance_key.

    NOTE: Smule's public API currently caps this endpoint at ~25 unique
    recordings per user (it returns the same set regardless of offset).
    We detect this by tracking which performance_keys we've already seen
    and stopping as soon as a page adds no new entries.

    Args:
        username:   Smule handle
        max_pages:  Safety limit — stop after this many pages

    Returns:
        A deduplicated list of performance dictionaries.
    """
    all_performances = []  # Start with an empty list
    # A Python "set" stores unique values; lookups are very fast (O(1))
    seen_keys = set()
    next_offset = 0
    page = 0

    print(f"[API] Fetching performances for @{username}...")

    while page < max_pages:
        data = get_performances(username, next_offset)

        if not data:
            break

        performances = data.get("list", [])
        if not performances:
            break

        # Filter out performances we've already seen
        new_perfs = []
        for p in performances:
            key = p.get("performance_key") or p.get("key")
            if key and key not in seen_keys:
                seen_keys.add(key)
                new_perfs.append(p)

        if not new_perfs:
            # No new unique performances on this page — we've seen everything
            print(f"[API]   No new performances on page {page + 1} — stopping.")
            break

        all_performances += new_perfs
        page += 1
        print(f"[API]   Page {page}: {len(new_perfs)} new performances (total: {len(all_performances)})")

        next_offset = data.get("next_offset")
        if not next_offset:
            break

    return all_performances
