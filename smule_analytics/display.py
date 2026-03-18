# =============================================================================
# smule_analytics/display.py
#
# This module handles all terminal output using the `rich` library.
# Rich adds colors, tables, panels, and progress bars to the terminal.
#
# KEY PYTHON CONCEPTS IN THIS FILE:
#   - Importing from a library (from rich import ...)
#   - Building and printing tables
#   - String formatting
#   - Functions that take dicts as arguments
# =============================================================================

from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich         import box

# Create a single Console object we'll reuse throughout the module.
# Think of it like a fancier version of print().
console = Console()


def print_banner():
    """Print a welcome banner at startup."""
    console.print(Panel.fit(
        "[bold cyan]🎤  Smule Analytics Tool[/bold cyan]\n"
        "[dim]Pulling your singing data from Smule...[/dim]",
        border_style="cyan"
    ))
    console.print()


def print_profile(profile: dict):
    """
    Display user profile info in a styled panel.

    The {:,} format specifier in f-strings adds commas to large numbers:
        f"{1234567:,}"  →  "1,234,567"

    Args:
        profile: A profile dict from api.get_user_profile_from_page()
    """
    if not profile:
        console.print("[red]Could not load profile data.[/red]")
        return

    lines = [
        f"[bold white]@{profile.get('handle', '?')}[/bold white]"
        + (f"  {profile['name']}" if profile.get("name") else ""),
    ]

    if profile.get("follower_count"):
        lines.append(f"\n[cyan]Followers:[/cyan]    {profile['follower_count']:,}")
    if profile.get("following_count"):
        lines.append(f"[cyan]Following:[/cyan]    {profile['following_count']:,}")
    if profile.get("num_performances"):
        lines.append(f"[cyan]Performances:[/cyan] {profile['num_performances']:,}")
    if profile.get("location"):
        lines.append(f"[cyan]Location:[/cyan]     {profile['location']}")
    if profile.get("is_verified"):
        lines.append("[green]✓ Verified[/green]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold cyan]Profile[/bold cyan]",
        border_style="cyan"
    ))
    console.print()


def print_overview(classified: dict):
    """
    Print a quick overview table showing performance counts by type.

    Args:
        classified: Dict from analytics.classify_performances()
                    Keys: "solo", "duet", "group", "all"
    """
    table = Table(title="Performance Overview", box=box.ROUNDED, border_style="cyan")
    table.add_column("Type",  style="bold white")
    table.add_column("Count", justify="right", style="cyan")

    # .items() returns (key, value) pairs — we unpack with "label, perfs"
    for label, perfs in classified.items():
        if label == "all":
            continue
        table.add_row(label.title(), str(len(perfs)))

    table.add_row("[bold]Total[/bold]", f"[bold]{len(classified['all'])}[/bold]")
    console.print(table)
    console.print()


def print_stats_panel(stats: dict, label: str):
    """
    Display a summary statistics panel for one performance category.

    Args:
        stats:  Dict from analytics.compute_performance_stats()
        label:  Title (e.g. "Solo", "Duet")
    """
    if not stats:
        console.print(f"[yellow]No {label.lower()} data.[/yellow]\n")
        return

    lines = [
        f"[bold]Performances:[/bold]  {stats['total']:,}",
        f"[bold]❤  Total loves:[/bold]   {stats['total_loves']:,}",
        f"[bold]👂 Total listens:[/bold] {stats['total_listens']:,}",
        f"[bold]💬 Total comments:[/bold]{stats['total_comments']:,}",
        f"[bold]🎁 Total gifts:[/bold]   {stats['total_gifts']:,}",
        f"[bold]Avg loves / song:[/bold] {stats['avg_loves']:.1f}",
    ]
    if stats.get("date_range"):
        lines.append(f"[bold]Date range:[/bold]    {stats['date_range']}")

    console.print(Panel(
        "\n".join(lines),
        title=f"[bold green]{label}[/bold green]",
        border_style="green"
    ))
    console.print()


def print_top_songs_by_loves(stats: dict, label: str = ""):
    """
    Print a table of the most-loved performances.

    Args:
        stats:  Dict from analytics.compute_performance_stats()
        label:  Optional label suffix
    """
    top = stats.get("top_by_loves", [])
    if not top:
        return

    title = f"Top Performances by Loves{' — ' + label if label else ''}"
    table = Table(title=title, box=box.ROUNDED, border_style="magenta")
    table.add_column("#",           style="dim", width=3)
    table.add_column("Song",        style="bold white", max_width=38)
    table.add_column("Artist",      style="italic", max_width=20)
    table.add_column("❤",           justify="right", style="red")
    table.add_column("👂",          justify="right", style="blue")
    table.add_column("💬",          justify="right", style="yellow")

    # enumerate() gives both the index and the item in a loop
    for i, p in enumerate(top, start=1):
        s = p.get("stats", {}) or {}
        table.add_row(
            str(i),
            p.get("title",  "Unknown"),
            p.get("artist", "Unknown") or "—",
            f"{s.get('total_loves',    0):,}",
            f"{s.get('total_listens',  0):,}",
            f"{s.get('total_comments', 0):,}",
        )

    console.print(table)
    console.print()


def print_most_sung_songs(stats: dict, label: str = ""):
    """Print a table of songs recorded most often."""
    songs = stats.get("most_sung_songs", [])
    if not songs:
        return

    title = f"Most Recorded Songs{' — ' + label if label else ''}"
    table = Table(title=title, box=box.ROUNDED, border_style="cyan")
    table.add_column("Rank",  style="dim", width=4)
    table.add_column("Song Title", style="bold white", max_width=45)
    table.add_column("Times", justify="right", style="cyan")

    # songs is a list of (title, count) tuples from Counter.most_common()
    for rank, (title, count) in enumerate(songs, start=1):
        table.add_row(str(rank), title, str(count))

    console.print(table)
    console.print()


def print_top_artists(stats: dict, label: str = ""):
    """Print a table of the artists you've sung most."""
    artists = stats.get("top_artists", [])
    if not artists:
        return

    title = f"Favourite Artists{' — ' + label if label else ''}"
    table = Table(title=title, box=box.ROUNDED, border_style="blue")
    table.add_column("Rank",   style="dim", width=4)
    table.add_column("Artist", style="bold white", max_width=40)
    table.add_column("Songs",  justify="right", style="blue")

    for rank, (artist, count) in enumerate(artists, start=1):
        table.add_row(str(rank), artist, str(count))

    console.print(table)
    console.print()


def print_top_partners(stats: dict):
    """Print a table of most frequent duet partners."""
    partners = stats.get("top_partners", [])
    if not partners:
        return

    table = Table(title="Most Frequent Duet Partners", box=box.ROUNDED, border_style="yellow")
    table.add_column("Rank",    style="dim", width=4)
    table.add_column("Partner", style="bold white")
    table.add_column("Duets",   justify="right", style="yellow")

    for rank, (handle, count) in enumerate(partners, start=1):
        table.add_row(str(rank), f"@{handle}", str(count))

    console.print(table)
    console.print()
