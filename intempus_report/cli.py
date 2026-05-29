"""CLI entry point for intempus-report."""

from __future__ import annotations

import calendar
import sys
from datetime import date

import click

from .config import load_config
from .api import IntempusClient
from .report import build_report
from .output import format_table, format_csv, format_json


def _parse_month(ctx: click.Context, param: click.Parameter, value: str | None) -> tuple[int, int]:
    if value is None:
        today = date.today()
        return today.year, today.month
    try:
        year_str, month_str = value.split("-")
        year, month = int(year_str), int(month_str)
        if not (1 <= month <= 12):
            raise ValueError
        return year, month
    except (ValueError, AttributeError):
        raise click.BadParameter("Expected format: YYYY-MM (e.g. 2026-05)", param=param)


@click.command()
@click.option(
    "--month",
    "-m",
    default=None,
    metavar="YYYY-MM",
    callback=_parse_month,
    is_eager=False,
    expose_value=True,
    help="Month to report (default: current month). Format: YYYY-MM",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "csv", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(),
    help="Path to config file (default: ~/.config/intempus/config.toml).",
)
@click.option(
    "--include-zero",
    is_flag=True,
    default=False,
    help="Include projects with 0 hours in the output.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Print raw HTTP requests/responses to stderr for troubleshooting.",
)
def main(
    month: tuple[int, int],
    output_format: str,
    config_path: str | None,
    include_zero: bool,
    debug: bool,
) -> None:
    """Show hours per project for the chosen month from Intempus."""
    from pathlib import Path

    cfg = load_config(Path(config_path) if config_path else None)

    year, mon = month
    month_name = calendar.month_name[mon]

    try:
        with IntempusClient(cfg.auth, debug=debug) as client:
            client.login()
            raw = client.fetch_month_report(year, mon)
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    report = build_report(year, mon, raw, bonus_cfg=cfg.bonus, include_zero=include_zero)

    if not report.entries:
        click.echo(f"No registrations found for {month_name} {year}.")
        sys.exit(0)

    if output_format == "table":
        format_table(report)
    elif output_format == "csv":
        click.echo(format_csv(report), nl=False)
    elif output_format == "json":
        click.echo(format_json(report))
