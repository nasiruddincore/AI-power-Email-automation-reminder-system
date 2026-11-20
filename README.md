🌈📧 AI power + email-automation-reminder-systemAutomated Email Dispatch, Smart Scheduling, Dry-Run Simulation & Multi-Color Streamlit Command Center📌 Extended Project DescriptionThe AI power + email-automation-reminder-system (Email Automation & Reminder System) is an industry-oriented workflow automation platform designed to eliminate manual follow-ups, missed deadlines, and repetitive communication bottlenecks across operations, HR, sales, and training teams. By ingesting structured contact lists and reminder schedules from CSV files, the system dynamically personalizes subject lines and message bodies, evaluates one-off (once), daily, and weekly recurrence rules, and dispatches notifications over encrypted SMTP (STARTTLS) or a safe zero-risk DRY_RUN simulation mode—ensuring students and teams can test full end-to-end automation without needing enterprise mail servers.Built with a clean, modular Python architecture (src/config.py, src/loader.py, src/personalizer.py, src/scheduler.py, src/mailer.py, and src/reporter.py), the project pairs a reliable CLI/background worker (main.py) with a modernized, multi-color Streamlit Command Center (app.py). Users can edit contacts and reminders live in the browser, preview personalized email templates in real time, monitor dispatch analytics via interactive Plotly charts and a PyDeck recipient map, inspect execution logs (logs/automation.log), and export timestamped CSV delivery reports (outputs/delivery_report_*.csv)—making it a complete, portfolio-ready proof of work on GitHub.🧩 Problem Statement & Solution⚠️ Challenge✅ Automated SolutionManual Follow-Up Fatigue: Sending individual reminders for classes, meetings, invoices, or onboarding wastes hours.CSV-Driven Batch Engine: Reads contacts.csv and reminders.csv via Pandas and personalizes every message automatically.Risk of Accidental Live Sends: Testing scripts against real inboxes can send broken templates.Safe Dry-Run Simulation (DRY_RUN=true): Simulates full execution, logging, and CSV reporting without touching external SMTP servers.Zero Delivery Visibility: Ad-hoc scripts fail silently when an email address is invalid or network drops.Audit Logs & CSV Reports: Captures SENT, DRY_RUN, and FAILED statuses with exact error reasons in logs/ and outputs/.Command-Line Only Barrier: Non-technical teammates cannot easily edit templates or view metrics.Multi-Color Streamlit Studio (app.py): Provides live CSV editors, template preview, Plotly charts, and a PyDeck contact map.🏛️ System Architecture & Data Flow┌────────────────────┐   ┌────────────────────┐   ┌──────────────────────────┐
│ data/contacts.csv  │   │ data/reminders.csv │   │ templates/               │
│ (id,name,email,    │   │ (id,contact_id,    │   │  reminder_template.txt   │
│  role,city,lat,lon)│   │  title,due_at,freq)│   │ (Subject + {placeholders})│
└─────────┬──────────┘   └─────────┬──────────┘   └────────────┬─────────────┘
          │                        │                           │
          └────────────┬───────────┴───────────────────────────┘
                       ▼
        ┌──────────────────────────────┐
        │  Data Loader & Validator     │  ──► src/loader.py (Pandas + datetime)
        └──────────────┬───────────────┘
                       ▼
        ┌──────────────────────────────┐
        │  Safe Template Personalizer  │  ──► src/personalizer.py (SafeDict)
        └──────────────┬───────────────┘
                       ▼
        ┌──────────────────────────────┐
        │  Due & Recurrence Scheduler  │  ──► src/scheduler.py (once/daily/weekly)
        └──────────────┬───────────────┘
                       ▼
        ┌──────────────────────────────┐
        │  SMTP / Dry-Run Mail Engine  │  ──► src/mailer.py (smtplib + STARTTLS)
        └───────┬──────────────┬───────┘
                │              │
    (DRY_RUN=true/false)       ▼
                │     ┌────────────────────────────────────────┐
                │     │  Observability & Reporting             │
                │     │  • logs/automation.log                 │
                │     │  • outputs/delivery_report_*.csv       │
                │     │  • app.py (Multi-Color Streamlit UI)   │
                │     └────────────────────────────────────────┘
                ▼
     [Simulated / Real Inbox]

✨ Key Features🧪 Safe Dry-Run & Live SMTP Modes: Toggle between risk-free local simulation (DRY_RUN=true) and authenticated STARTTLS email delivery (DRY_RUN=false).🎨 Multi-Color Streamlit Command Center (app.py): Gradient hero header, color-coded KPI cards, interactive Plotly charts, and a PyDeck recipient location map.📝 In-Browser CSV & Template Editors: Edit contacts.csv, reminders.csv, and reminder_template.txt directly in the UI with instant live message previews.⏰ Flexible Scheduling (main.py): Supports once, daily, and weekly reminders, --now immediate batch execution, and --loop continuous polling.🛡️ Resilient Error Handling: Validates email syntax, handles missing template keys gracefully via SafeDict, and isolates per-row SMTP/network exceptions.📊 Automated Reports & Logs: Saves structured logs to logs/automation.log and timestamped delivery reports to outputs/delivery_report_YYYYMMDD_HHMMSS.csv.🛠️ Tech StackCore Language: Python 3.10+Data & Scheduling: pandas, schedule, datetimeEmail & Security: smtplib, email.message, python-dotenv, loggingDashboard & Visualization: streamlit, plotly, pydeck📂 Project Folder StructureEmail-Automation-Reminder-System/
│
├── .streamlit/
│   └── config.toml               # Streamlit theme configuration
├── data/
│   ├── contacts.csv              # Recipient list with role & city coordinates
│   └── reminders.csv             # Scheduled reminders (once, daily, weekly)
├── templates/
│   └── reminder_template.txt     # Email subject & body template with {placeholders}
├── src/
│   ├── __init__.py               # Package initializer
│   ├── config.py                 # Environment & path configuration
│   ├── loader.py                 # CSV & template loader with validation
│   ├── personalizer.py           # Safe placeholder substitution engine
│   ├── scheduler.py              # Recurrence & due-window evaluator
│   ├── mailer.py                 # SMTP STARTTLS & dry-run sender
│   └── reporter.py               # Timestamped CSV report generator
├── outputs/
│   └── .gitkeep                  # Generated delivery_report_*.csv files
├── logs/
│   └── .gitkeep                  # Runtime automation.log file
├── images/
│   └── .gitkeep                  # Portfolio & UI screenshots
├── docs/
│   └── architecture.md           # System design notes
├── app.py                        # Multi-Color Streamlit Web Dashboard
├── main.py                       # CLI & background scheduler entry point
├── requirements.txt              # Python package dependencies
├── .env.example                  # Safe environment variable template
├── .gitignore                    # Excludes .env, venv/, logs/*.log, outputs/*.csv
└── README.md                     # Project documentation

💻 PowerShell Setup & Execution Guide (Windows)Open Windows PowerShell in your project directory (Email-Automation-Reminder-System) and run the following commands step by step:1️⃣ Create & Activate Virtual Environmentpython -m venv venv
.\venv\Scripts\Activate.ps1

(If PowerShell blocks script activation, run Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass first, or prefix commands with .\venv\Scripts\python.exe -m.)2️⃣ Install Dependenciespython -m pip install --upgrade pip
python -m pip install -r requirements.txt

3️⃣ Configure Environment Variables (.env)Copy-Item .env.example .env

Edit .env if you want to test real SMTP delivery (keep DRY_RUN=true for safe simulation):DRY_RUN=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_demo_email@gmail.com
SMTP_PASS=your_16_char_app_password
SENDER_NAME=Automation Reminder Bot
SENDER_EMAIL=your_demo_email@gmail.com
POLL_INTERVAL_SECONDS=30

4️⃣ Run the Multi-Color Streamlit Dashboard (app.py)python -m streamlit run app.py

Open http://localhost:8501 in your browser to run batches, edit CSVs, preview templates, and view interactive charts and the contact map.5️⃣ Run the CLI & Background Scheduler (main.py)# 1. Dry-run all sample reminders immediately
python main.py --now --dry-run

# 2. Check and process only reminders currently due
python main.py --now

# 3. Run continuous background scheduler loop (Press Ctrl+C to stop)
python main.py --loop --dry-run

# 4. Run live SMTP delivery (requires valid credentials in .env)
python main.py --now --live

📊 Sample Terminal & Report Output2026-11-20 10:05:01 | INFO     | src.loader | Loaded 4 valid contacts from contacts.csv
2026-11-20 10:05:01 | INFO     | src.loader | Loaded 4 reminders from reminders.csv
2026-11-20 10:05:01 | INFO     | src.mailer | [DRY-RUN] To: aarav.demo@example.com | Subject: Reminder: Submit Python Assignment #3 (Due: 2026-11-20 18:00)
2026-11-20 10:05:01 | INFO     | src.reporter | Saved delivery report with 4 row(s) to outputs/delivery_report_20261120_100501.csv
2026-11-20 10:05:01 | INFO     | main | Batch complete -> Total: 4 | SENT: 0 | DRY_RUN: 4 | FAILED: 0

📸 Screenshots & Proof of WorkSave your captured screenshots inside images/ to showcase on GitHub:images/streamlit_dashboard.png — Multi-Color Streamlit Command Center & KPI Cardsimages/map_and_charts.png — Plotly Analytics & PyDeck Recipient Mapimages/template_studio.png — Live Personalized Email Previewimages/dry_run_terminal.png — PowerShell CLI Dry-Run & Report Output🔐 Security Best PracticesNever commit .env or real Gmail App Passwords to GitHub.Always share .env.example with placeholder values so others can configure the project safely..gitignore automatically excludes .env, venv/, __pycache__/, logs/*.log, and outputs/*.csv.🎯 Career & Industry RelevanceThis project demonstrates practical engineering competencies for Python Developer, Automation Engineer, Operations Analyst, HR/Admin Tech, and Business Productivity roles—covering structured ETL pipelines, template rendering, job scheduling, SMTP protocol integration, fault-tolerant logging, and interactive BI dashboarding.
