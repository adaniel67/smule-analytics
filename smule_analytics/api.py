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
#   - while loops with a break condition
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
#
# Fetches one "page" (25 recordings) from the Smule "legacy" JSON endpoint.
#
# URL format:  /cacophonoussound/recordings/json?offset=0
#              /cacophonoussound/recordings/json?offset=25
#              /cacophonoussound/recordings/json?offset=50  ... and so on
#
# This endpoint genuinely paginates — each call with a new offset returns
# a different batch of recordings, unlike the older endpoint we previously
# used which returned the same 25 results regardless of the offset value.
# ---------------------------------------------------------------------------
def get_performances(username: str, offset: int = 0) -> dict | None:
    """
    Fetch one page of performances (25 recordings) for a user.

    Args:
        username: Smule handle (e.g. "cacophonoussound")
        offset:   Where to start — 0 = first 25, 25 = next 25, etc.

    Returns:
        A dict with "list" (performances) and "next_offset", or None on error.
    """
    # The "legacy" JSON endpoint: no authentication required, real pagination.
    # We discovered this by studying open-source Smule analytics projects
    # and verifying it returns unique data at each offset.
    url = f"{BASE_URL}/{username}/recordings/json"

    # Query parameters become the URL query string: ?offset=0&limit=25
    # requests handles the URL encoding for us automatically.
    params = {"offset": offset}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"[API] HTTP error fetching performances at offset {offset}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        # RequestException is the base class for all requests errors
        print(f"[API] Error: {e}")
        return None


# ---------------------------------------------------------------------------
# FUNCTION: get_all_performances
#
# Repeatedly calls get_performances() with increasing offsets until Smule
# tells us there are no more recordings to fetch.
#
# KEY PYTHON CONCEPTS:
#   - while loop  (keeps looping until a condition becomes False)
#   - break       (exits the loop immediately)
#   - list +=     (extends a list in-place by appending another list)
#   - set         (stores unique values; lookups are O(1) — very fast)
# ---------------------------------------------------------------------------
def get_all_performances(username: str, max_pages: int = 100) -> list:
    """
    Fetch every available recording for a user, using real pagination.

    Args:
        username:   Smule handle
        max_pages:  Safety ceiling — stop after this many pages (25 each)
                    Default 100 = up to 2,500 recordings.

    Returns:
        A list of all performance dictionaries, oldest to newest or
        however Smule returns them.
    """
    all_performances = []  # Grows as we fetch each page
    seen_keys        = set()  # Tracks performance_key values we've already added
    offset           = 0      # Start at the very first recording
    page             = 0      # Counter just for the console progress output

    print(f"[API] Fetching all recordings for @{username}...")

    # A while loop keeps running until we decide to break out of it.
    while page < max_pages:
        data = get_performances(username, offset=offset)

        # If the request failed entirely, stop trying
        if data is None:
            print("[API] Request failed — stopping.")
            break

        performances = data.get("list", [])

        # An empty list means we've gone past the last recording
        if not performances:
            print(f"[API] Empty page at offset {offset} — all recordings fetched.")
            break

        # ---------------------------------------------------------------
        # Deduplication safety net
        # Even with proper pagination we guard against accidental repeats.
        # We use a set() here because checking "key in set" is O(1)
        # (constant time), whereas "key in list" is O(n) (gets slower as
        # the list grows). This matters when we have thousands of items.
        # ---------------------------------------------------------------
        new_perfs = []
        for p in performances:
            # "performance_key" is the unique ID Smule uses for each recording
            key = p.get("performance_key") or p.get("key")
            if key and key not in seen_keys:
                seen_keys.add(key)
                new_perfs.append(p)

        # If every item on this page is a duplicate, we've truly hit the end
        if not new_perfs:
            print(f"[API] All items on page {page + 1} were duplicates — stopping.")
            break

        # += on a list appends every item from new_perfs to all_performances
        all_performances += new_perfs
        page  += 1
        offset = data.get("next_offset", offset + 25)

        print(f"[API]   Page {page:3d} (offset {offset - 25:4d}): "
              f"+{len(new_perfs):2d} recordings  |  total so far: {len(all_performances)}")

        # A next_offset of None or 0 (when we're not at the start) means done.
        # We check "offset > 0" to avoid stopping on the very first page.
        if not data.get("next_offset") and page > 0:
            print("[API] No next_offset returned — all recordings fetched.")
            break

    print(f"[API] Done. Total recordings fetched: {len(all_performances)}")
    return all_performances
