# 📧 Email Automation & Reminder System

A modular Python automation tool that reads contact and reminder CSV files, personalizes email templates, evaluates one-off or recurring reminders, sends messages over SMTP (with a safe dry-run simulation mode), writes structured logs, and generates CSV delivery reports.

## 📌 Project Overview
Manual follow-ups, deadline reminders, and recurring notifications are error-prone when handled by hand. This project provides a clean, configurable automation workflow designed for students, developers, operations teams, HR coordinators, and trainers who want reliable scheduled reminders without heavy enterprise software.

## ⚠️ Problem Statement
Teams and individuals frequently juggle repetitive reminders (deadlines, meetings, check-ins, follow-ups) across spreadsheets and chat threads. Without automation and delivery tracking, reminders get sent late, forgotten, or lack clear status records when something fails.

## 🏭 Industry Relevance
* **HR & Onboarding:** Interview reminders, onboarding task nudges, policy acknowledgments.
* **Sales & Operations:** Follow-up reminders, recurring status check-ins, vendor/client nudges.
* **Training & Education:** Class/workshop reminders, assignment due dates, session follow-ups.
* **Backend & Automation Roles:** Demonstrates CSV ingestion, template rendering, scheduling logic, SMTP error handling, environment security, and observability.

## ✨ Features
* **CSV-Driven Inputs:** Loads recipients from `data/contacts.csv` and schedules from `data/reminders.csv` using Pandas.
* **Template Personalization:** Merges contact and reminder fields (`{name}`, `{reminder_title}`, `{due_at}`, `{notes}`, etc.) safely without crashing on unmapped placeholders.
* **Flexible Scheduling:** Supports one-time (`once`), `daily`, and `weekly` reminders, plus `--now` immediate batch runs and `--loop` continuous polling.
* **Dry-Run & Live SMTP Modes:** Simulate runs safely with `DRY_RUN=true` or send real emails via SMTP with TLS (`smtplib` + `EmailMessage`).
* **Logging & CSV Reports:** Records execution history in `logs/automation.log` and exports timestamped CSV reports in `outputs/`.

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Data Processing:** `pandas`
* **Email & Scheduling:** `smtplib`, `email.message`, `schedule`, `datetime`
* **Configuration & Logging:** `python-dotenv`, `logging`

## 📂 Folder Structure
```text
Email-Automation-Reminder-System/
├── data/
│   ├── contacts.csv
│   └── reminders.csv
├── templates/
│   └── reminder_template.txt
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── loader.py
│   ├── personalizer.py
│   ├── scheduler.py
│   ├── mailer.py
│   └── reporter.py
├── outputs/
├── logs/
├── images/
├── docs/
├── .env.example
├── .gitignore
├── requirements.txt
└── main.py