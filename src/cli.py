import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import select
from datetime import date
from models import Job, SessionLocal, init_db

app = typer.Typer(no_args_is_help=True)
console = Console()

def _parse_date(s: str | None):
    if not s:
        return None
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)

@app.command(help="Create the database if it doesn't exist.")
def init():
    init_db()
    console.print("[green]Database ready[/green]")

@app.command(help="Add a job application.")
def add(
    title: str,
    company: str,
    link: str = typer.Option("", "--link", "-l", help="URL to job listing"),
    deadline: str = typer.Option("", "--deadline", "-d", help="YYYY-MM-DD"),
    notes: str = typer.Option("", "--notes", "-n", help="Any notes"),
    status: str = typer.Option("interested", "--status", "-s", help="interested/applied/interview/offer/rejected"),
):
    init_db()
    with SessionLocal() as s:
        j = Job(
            title=title,
            company=company,
            link=link or None,
            deadline=_parse_date(deadline),
            notes=notes or None,
            status=status,
        )
        s.add(j)
        s.commit()
        console.print(f"[green]Added[/green] {j.title} @ {j.company} (id={j.id})")

@app.command(help="List jobs (optionally filter by status).")
def list(status: str = typer.Option("", "--status", "-s")):
    init_db()
    with SessionLocal() as s:
        rows = s.execute(select(Job)).scalars().all()
        if status:
            rows = [r for r in rows if r.status == status]

        table = Table(title="Jobs", show_lines=True)
        for c in ["id", "title", "company", "status", "deadline", "link"]:
            table.add_column(c)
        for r in rows:
            table.add_row(
                str(r.id),
                r.title,
                r.company,
                r.status,
                r.deadline.isoformat() if r.deadline else "—",
                r.link or "—",
            )
        console.print(table)

@app.command(help="Update a job's status.")
def update(id: int, status: str):
    valid = {"interested", "applied", "interview", "offer", "rejected"}
    if status not in valid:
        console.print(f"[red]Invalid status.[/red] Use one of: {', '.join(sorted(valid))}")
        raise typer.Exit(1)
    with SessionLocal() as s:
        j = s.get(Job, id)
        if not j:
            console.print("[red]Not found[/red]"); raise typer.Exit(1)
        j.status = status
        s.commit()
        console.print(f"[yellow]Updated[/yellow] {id} -> {status}")

@app.command(help="Delete a job by ID.")
def remove(id: int):
    with SessionLocal() as s:
        j = s.get(Job, id)
        if not j:
            console.print("[red]Not found[/red]"); raise typer.Exit(1)
        s.delete(j); s.commit()
        console.print(f"[red]Removed[/red] {id}")

@app.command(help="Show details for a single job by ID.")
def detail(id: int):
    with SessionLocal() as s:
        j = s.get(Job, id)
        if not j:
            console.print("[red]Job not found[/red]")
            raise typer.Exit(1)

        table = Table(title=f"Job {j.id} Details", show_lines=True)
        table.add_column("Field")
        table.add_column("Value")

        table.add_row("ID", str(j.id))
        table.add_row("Title", j.title)
        table.add_row("Company", j.company)
        table.add_row("Status", j.status)
        table.add_row("Deadline", j.deadline.isoformat() if j.deadline else "—")
        table.add_row("Link", j.link or "—")
        table.add_row("Notes", j.notes or "—")

        console.print(table)

import csv
from pathlib import Path

@app.command(help="Export all jobs to a CSV file.")
def export(filename: str = "jobs_export.csv"):
    init_db()
    with SessionLocal() as s:
        rows = s.execute(select(Job)).scalars().all()

        if not rows:
            console.print("[yellow]No jobs to export[/yellow]")
            return

        filepath = Path(filename)
        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # header
            writer.writerow(["id", "title", "company", "status", "deadline", "link", "notes"])
            # rows
            for r in rows:
                writer.writerow([
                    r.id,
                    r.title,
                    r.company,
                    r.status,
                    r.deadline.isoformat() if r.deadline else "",
                    r.link or "",
                    r.notes or "",
                ])

        console.print(f"[green]Exported {len(rows)} jobs to {filepath}[/green]")

@app.command(help="Search jobs by keyword in title, company, or notes.")
def search(keyword: str):
    init_db()
    kw = keyword.lower()
    with SessionLocal() as s:
        rows = s.execute(select(Job)).scalars().all()

        def match(r: Job) -> bool:
            fields = [
                (r.title or "").lower(),
                (r.company or "").lower(),
                (r.notes or "").lower(),
            ]
            return any(kw in f for f in fields)

        results = [r for r in rows if match(r)]

        if not results:
            console.print(f"[yellow]No jobs found for '{keyword}'[/yellow]")
            return

        table = Table(title=f"Search results for '{keyword}'", show_lines=True)
        for c in ["id", "title", "company", "status", "deadline", "link"]:
            table.add_column(c)
        for r in results:
            table.add_row(
                str(r.id),
                r.title,
                r.company,
                r.status,
                r.deadline.isoformat() if r.deadline else "—",
                r.link or "—",
            )
        console.print(table)


# 👇 keep this at the very bottom of cli.py
if __name__ == "__main__":
    app()