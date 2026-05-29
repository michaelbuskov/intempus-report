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

The config file lives at `~/.config/intempus/config.toml`.  
The tool creates a commented template on first run if the file does not exist.

### Auth (required)

```toml
[auth]
base_url = "https://intempus.dk"
username = "your@email.com"
password = "yourpassword"
```

| Field | Description |
|---|---|
| `base_url` | Base URL of your Intempus instance (default: `https://intempus.dk`) |
| `username` | Your Intempus login email |
| `password` | Your Intempus login password |

### Bonus (optional)

If your company pays a bonus based on billable hours, add a `[bonus]` section to unlock bonus calculations in the output:

```toml
[bonus]
hourly_rate = 1000.0   # rate charged to the customer (in your salary currency)
min_hours   = 120.0    # hours threshold — bonus only applies to hours above this
projects = [
  "Backend API",
  "Code Review",
]
```

| Field | Required | Description |
|---|---|---|
| `hourly_rate` | ✅ | The hourly rate billed to the customer |
| `min_hours` | ❌ | Minimum hours before bonus kicks in (default: `0`) |
| `projects` | ❌ | List of project names that count toward the bonus (default: all projects) |

Projects marked as bonus projects are shown with a ★ in the table output.

#### How the bonus is calculated

```
bonus_eligible_hours = bonus_hours − min_hours   (floored at 0)
expected_bonus       = bonus_eligible_hours × (hourly_rate × 0.49)
```

The formula assumes the employee receives 49% of the hourly rate for hours worked above the threshold.

**Example** — 140 h of bonus-project hours, threshold 120 h, rate 1 000:

```
bonus_eligible_hours = 140 − 120 = 20 h
expected_bonus       = 20 × (1 000 × 0.49) = 9 800
```

The table output with a bonus section looks like this:

```
Hours per project — May 2026
╭───────────────────────────┬───────────╮
│ Project                   │ Hours     │
├───────────────────────────┼───────────┤
│ Backend API ★             │  112.0 h  │
│ Code Review ★             │   28.0 h  │
│ Meetings / Admin          │   12.0 h  │
├───────────────────────────┼───────────┤
│ Total                     │  152.0 h  │
├───────────────────────────┼───────────┤
│ Bonus hours (★)           │  140.0 h  │
│   Threshold               │  120.0 h  │
│   Bonus-eligible hours    │   20.0 h  │
│ Expected bonus            │   9,800   │
╰───────────────────────────┴───────────╯
  (Bonus = (140.0 h − 120.0 h) × 1,000 × 49%)
```

---

## Usage

```
intempus-report [OPTIONS]

Options:
  -m, --month YYYY-MM   Month to report (default: current month)
  -f, --format          Output format: table (default), csv, json
      --include-zero    Show projects with 0 hours
      --config PATH     Custom config file path
      --debug           Print raw HTTP requests/responses to stderr
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
