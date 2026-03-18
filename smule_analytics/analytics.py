# =============================================================================
# smule_analytics/analytics.py
#
# This module takes raw performance data (lists of dictionaries) and computes
# useful statistics from it.
#
# KEY PYTHON CONCEPTS IN THIS FILE:
#   - List comprehensions  [ x for x in list if condition ]
#   - Dictionary operations
#   - Sorting with sorted() and key=
#   - sum(), len(), max(), min()
#   - The Counter class for counting occurrences
#   - Handling missing/None values with .get() and "or"
# =============================================================================

from collections import Counter  # Standard library — counts items in a list
from datetime import datetime     # Standard library — parse dates and times


def classify_performances(performances: list) -> dict:
    """
    Split a flat list of performances into groups by ensemble_type.

    Smule's API mixes solos, duets, and group recordings together.
    This function separates them using a list comprehension with a filter.

    A list comprehension like:
        [p for p in performances if p["ensemble_type"] == "SOLO"]
    is shorthand for building a new list containing only items that pass a test.

    Args:
        performances: Raw list from the Smule API

    Returns:
        A dict with keys "solo", "duet", "group", "all"
    """
    return {
        # "SOLO" — the user recorded alone
        "solo":  [p for p in performances if p.get("ensemble_type") == "SOLO"],
        # "DUET" — the user sang with one other person
        "duet":  [p for p in performances if p.get("ensemble_type") == "DUET"],
        # "GROUP" — three or more performers
        "group": [p for p in performances if p.get("ensemble_type") == "GROUP"],
        # "all"  — every performance regardless of type
        "all":   performances,
    }


def compute_performance_stats(performances: list, username: str = "") -> dict:
    """
    Given a list of performance dicts, compute summary statistics.

    Args:
        performances: A list of performance dicts (already filtered or not)

    Returns:
        A dictionary of computed statistics.
    """
    if not performances:
        return {}

    # --- Extract individual metrics using list comprehensions ---
    # .get("stats", {}) returns an empty dict if "stats" key is missing.
    # "or 0" converts None to 0 — needed because some fields can be None.
    loves    = [p.get("stats", {}).get("total_loves",    0) or 0 for p in performances]
    listens  = [p.get("stats", {}).get("total_listens",  0) or 0 for p in performances]
    comments = [p.get("stats", {}).get("total_comments", 0) or 0 for p in performances]
    gifts    = [p.get("stats", {}).get("total_gifts",    0) or 0 for p in performances]

    # --- Top 5 most loved performances ---
    # sorted() returns a NEW sorted list.
    # key=lambda p: ... tells it what value to sort by.
    # reverse=True means highest first.
    top_by_loves = sorted(
        performances,
        key=lambda p: p.get("stats", {}).get("total_loves", 0) or 0,
        reverse=True
    )[:5]  # [:5] = "slice from start to index 5" — first 5 items

    # --- Count how many times each song title appears ---
    titles = [p.get("title", "Unknown") for p in performances]
    title_counts = Counter(titles)  # Counter({'Song A': 3, 'Song B': 2, ...})

    # --- Count most frequent duet partners ---
    # Smule performances come in two forms:
    #   A) User created the invite → they are "owner", partner is in "other_performers"
    #   B) User joined someone else → they appear in "other_performers", partner is "owner"
    # To get the real partner in both cases we collect everyone who is NOT the user.
    user_handle_lower = username.lower()

    partners = []
    for p in performances:
        owner_handle = (p.get("owner") or {}).get("handle", "")
        # Include the owner if the user is NOT the owner (case B above)
        if owner_handle and owner_handle.lower() != user_handle_lower:
            partners.append(owner_handle)
        # Include other_performers who are NOT the user themselves (case A + any group)
        for performer in p.get("other_performers") or []:
            handle = performer.get("handle", "")
            if handle and handle.lower() != user_handle_lower:
                partners.append(handle)
    partner_counts = Counter(partners)

    # --- Songs by artist ---
    artists = [p.get("artist", "Unknown") or "Unknown" for p in performances]
    artist_counts = Counter(artists)

    # --- Calculate date range ---
    dates = []
    for p in performances:
        created = p.get("created_at", "")
        if created:
            try:
                # datetime.fromisoformat() parses a date string like "2026-03-17T07:32:48-07:00"
                dates.append(datetime.fromisoformat(created))
            except ValueError:
                pass  # Skip unparseable dates

    date_range = None
    if dates:
        earliest = min(dates)
        latest   = max(dates)
        # strftime() formats a datetime as a human-readable string
        date_range = f"{earliest.strftime('%b %Y')} → {latest.strftime('%b %Y')}"

    return {
        "total":          len(performances),
        "total_loves":    sum(loves),
        "total_listens":  sum(listens),
        "total_comments": sum(comments),
        "total_gifts":    sum(gifts),
        # Conditional expression: value if condition else fallback
        "avg_loves":    sum(loves)   / len(loves)   if loves   else 0,
        "avg_listens":  sum(listens) / len(listens) if listens else 0,
        "top_by_loves":      top_by_loves,
        "most_sung_songs":   title_counts.most_common(10),
        "top_partners":      partner_counts.most_common(10),
        "top_artists":       artist_counts.most_common(10),
        "date_range":        date_range,
    }
