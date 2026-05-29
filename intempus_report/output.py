"""Output formatting: rich table, CSV, JSON."""

from __future__ import annotations

import csv
import io
import json
import calendar

from rich.console import Console
from rich.table import Table
from rich import box

from .report import Report

console = Console()


def format_table(report: Report) -> None:
    month_name = calendar.month_name[report.month]
    title = f"Hours per project — {month_name} {report.year}"

    has_bonus = report.bonus_cfg is not None

    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Project", style="cyan")
    table.add_column("Hours", justify="right", style="green")

    for entry in report.entries:
        marker = " ★" if entry.bonus else ""
        table.add_row(f"{entry.name}{marker}", f"{entry.hours:.1f} h")

    # Total row
    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{report.total_hours:.1f} h[/bold]")

    # Bonus rows
    if has_bonus:
        cfg_b = report.bonus_cfg  # type: ignore[union-attr]
        table.add_section()
        table.add_row(
            "[yellow]Bonus hours (★)[/yellow]",
            f"[yellow]{report.bonus_hours:.1f} h[/yellow]",
        )
        if cfg_b.min_hours > 0:
            table.add_row(
                "[dim]  Threshold[/dim]",
                f"[dim]{cfg_b.min_hours:.1f} h[/dim]",
            )
            table.add_row(
                "[yellow]  Bonus-eligible hours[/yellow]",
                f"[yellow]{report.bonus_eligible_hours:.1f} h[/yellow]",
            )
        bonus_str = f"{report.bonus_amount:,.0f}"
        table.add_row(
            "[bold yellow]Expected bonus[/bold yellow]",
            f"[bold yellow]{bonus_str}[/bold yellow]",
        )

    console.print()
    console.print(table)
    if has_bonus:
        cfg_b = report.bonus_cfg  # type: ignore[union-attr]
        rate = cfg_b.hourly_rate
        if cfg_b.min_hours > 0:
            console.print(
                f"  [dim](Bonus = ({report.bonus_hours:.1f} h − {cfg_b.min_hours:.1f} h) × {rate:,.0f} × 49%)[/dim]\n"
            )
        else:
            console.print(
                f"  [dim](Bonus = {report.bonus_hours:.1f} h × {rate:,.0f} × 49%)[/dim]\n"
            )
    else:
        console.print()


def format_csv(report: Report) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["project", "hours", "bonus_project"])
    for entry in report.entries:
        writer.writerow([entry.name, f"{entry.hours:.2f}", str(entry.bonus).lower()])
    writer.writerow(["TOTAL", f"{report.total_hours:.2f}", ""])
    if report.bonus_cfg is not None:
        writer.writerow(["BONUS HOURS", f"{report.bonus_hours:.2f}", ""])
        if report.bonus_cfg.min_hours > 0:
            writer.writerow(["THRESHOLD", f"{report.bonus_cfg.min_hours:.2f}", ""])
            writer.writerow(["BONUS-ELIGIBLE HOURS", f"{report.bonus_eligible_hours:.2f}", ""])
        writer.writerow(["EXPECTED BONUS", f"{report.bonus_amount:.2f}", ""])
    return output.getvalue()


def format_json(report: Report) -> str:
    import calendar as cal
    data: dict = {
        "year": report.year,
        "month": report.month,
        "month_name": cal.month_name[report.month],
        "total_hours": report.total_hours,
        "projects": [
            {"name": e.name, "hours": e.hours, "bonus_project": e.bonus}
            for e in report.entries
        ],
    }
    if report.bonus_cfg is not None:
        data["bonus_hours"] = report.bonus_hours
        data["bonus_eligible_hours"] = report.bonus_eligible_hours
        data["bonus_amount"] = report.bonus_amount
        data["hourly_rate"] = report.bonus_cfg.hourly_rate
        data["min_hours"] = report.bonus_cfg.min_hours
    return json.dumps(data, indent=2)

