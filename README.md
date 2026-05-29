# intempus-report

CLI tool that shows your **hours per project** for any month from [Intempus](https://intempus.dk/).

```
Hours per project — May 2026
╭───────────────────────────┬───────────╮
│ Project                   │ Hours     │
├───────────────────────────┼───────────┤
│ Backend API               │  32.5 h   │
│ Code Review               │   8.0 h   │
│ Meetings / Admin          │  12.0 h   │
├───────────────────────────┼───────────┤
│ Total                     │  52.5 h   │
╰───────────────────────────┴───────────╯
```

---

## Requirements

- Python 3.11+
- An Intempus account (username + password)

---

## Installation

```bash
cd intempus-report
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

The `intempus-report` command is now available inside the venv.

---

## Configuration

Create `~/.config/intempus/config.toml` (the tool will create a template on first run):

```toml
[auth]
base_url = "https://intempus.dk"
username = "your@email.com"
password = "yourpassword"
```

Replace `username` and `password` with your Intempus login credentials.
That's it — no API key hunting required.

---

## Usage

```
intempus-report [OPTIONS]

Options:
  -m, --month YYYY-MM   Month to report (default: current month)
  -f, --format          Output format: table (default), csv, json
  -w, --work-model INT  Work model ID (default: 1; only relevant if your
                        company uses multiple work models)
      --include-zero    Show projects with 0 hours
      --config PATH     Custom config file path
  --help                Show this message and exit.
```

### Examples

```bash
# Current month, pretty table
intempus-report

# Specific month
intempus-report --month 2026-03

# Export as CSV
intempus-report --month 2026-05 --format csv > may_2026.csv

# JSON (pipe to jq for further processing)
intempus-report --format json | jq '.projects'
```

---

## How it works

The tool authenticates with the Intempus web app using your email and password,
then calls the internal `/web/v1/work_category/get_month_work_report/` endpoint,
which returns hours already aggregated by work category (project) for the chosen date range.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Login failed — check your username and password` | Wrong credentials in config |
| `No csrftoken cookie found` | Intempus may have changed their login flow; open an issue |
| `No registrations found` | You have no time entries for that month, or try `--work-model 2` if your company uses multiple work models |

---

## License

MIT
