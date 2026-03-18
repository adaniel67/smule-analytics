# =============================================================================
# main.py  —  Smule Analytics Tool
#
# This is the ENTRY POINT of the program — where execution starts.
# Run it with:  python main.py
#
# The code is organized across three modules (files in the smule_analytics/
# folder), each with a clear responsibility:
#
#   api.py       — fetches data from Smule's website
#   analytics.py — computes statistics from raw data
#   display.py   — prints results nicely in the terminal
#
# This separation is called "separation of concerns" — a key principle in
# software design. Each module does one job and does it well.
#
# KEY PYTHON CONCEPTS IN THIS FILE:
#   - Importing from your own modules
#   - Calling functions in sequence
#   - if __name__ == "__main__"  (explained at the bottom)
# =============================================================================

# Import from our own package (the smule_analytics/ folder)
from smule_analytics import api, analytics, display


# ---------------------------------------------------------------------------
# CONFIG — change these to analyze a different account or fetch more pages
# ---------------------------------------------------------------------------
USERNAME  = "cacophonoussound"
MAX_PAGES = 200   # Each page = 25 performances; 200 pages = up to 5,000 recordings


def run():
    """
    Main function — orchestrates all the steps in order:
      1. Show a welcome banner
      2. Fetch and display the user's profile
      3. Fetch all performances (paginated)
      4. Split them by type (solo / duet / group)
      5. Compute statistics for each type
      6. Display all the results
    """

    # Step 1: Welcome banner
    display.print_banner()

    # -------------------------------------------------------------------------
    # Step 2: Profile
    # -------------------------------------------------------------------------
    profile = api.get_user_profile_from_page(USERNAME)
    display.print_profile(profile)

    # -------------------------------------------------------------------------
    # Step 3: Fetch all performances (calls the Smule API multiple times)
    # -------------------------------------------------------------------------
    all_perfs = api.get_all_performances(USERNAME, max_pages=MAX_PAGES)

    if not all_perfs:
        display.console.print("[red]No performances found. Check the username and try again.[/red]")
        return

    print()  # blank line for readability

    # -------------------------------------------------------------------------
    # Step 4: Classify performances by type
    # Returns a dict with keys: "solo", "duet", "group", "all"
    # -------------------------------------------------------------------------
    classified = analytics.classify_performances(all_perfs)
    display.print_overview(classified)

    # -------------------------------------------------------------------------
    # Step 5 & 6: Stats and tables — for each performance type
    # -------------------------------------------------------------------------
    for label, perfs in classified.items():
        if label == "all" or not perfs:
            continue

        label_title = label.title()  # .title() capitalizes the first letter: "solo" → "Solo"

        # Compute statistics for this group (pass USERNAME to filter self from partners)
        stats = analytics.compute_performance_stats(perfs, username=USERNAME)

        # Display a summary panel
        display.print_stats_panel(stats, label=f"{label_title} Performances")

        # Display detailed tables
        display.print_top_songs_by_loves(stats, label=label_title)
        display.print_most_sung_songs(stats, label=label_title)
        display.print_top_artists(stats, label=label_title)

        # Show partner table for duets only
        if label == "duet":
            display.print_top_partners(stats)

    display.console.print("[bold green]Done! ✅[/bold green]\n")


# ---------------------------------------------------------------------------
# if __name__ == "__main__"
#
# Python sets __name__ to "__main__" only when you run this file directly
# (e.g. `python main.py`). If another file imports main.py, this block
# won't run automatically. This is the standard Python entry point pattern.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run()
