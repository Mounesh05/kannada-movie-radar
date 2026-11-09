# 🎬 Kannada Movie Radar

### Automated Kannada Cinema News Aggregation & Weekly Telegram Digest

**Python 3.12 · PostgreSQL · Neon · GitHub Actions · Telegram Bot API · Gemini AI**

Kannada Movie Radar is a cloud-based news aggregation and delivery system designed to collect Kannada cinema updates, organize articles, prevent duplicate records, and deliver a weekly news digest through Telegram.

The project combines automated data ingestion, rule-based classification, optional AI-powered information extraction, PostgreSQL storage, and scheduled cloud workflows.

It is developed as an academic software engineering project with an emphasis on **automation, data processing, database design, and reliable cloud execution**.

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?logo=github)](https://github.com/Mounesh05/kannada-movie-radar)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql)
![GitHub Actions](https://img.shields.io/badge/Automation-GitHub_Actions-2088FF?logo=githubactions)

---

## 📌 Project Overview

Kannada cinema news is distributed across various entertainment websites, making it inconvenient to follow multiple sources regularly.

**Kannada Movie Radar** addresses this by providing a centralized, automated workflow:

1. Retrieve recent Kannada cinema news from configured RSS feeds.
2. Normalize article titles, URLs, and publication dates.
3. Identify potentially relevant cinema updates.
4. Store articles in PostgreSQL and prevent duplicates.
5. Generate a weekly news digest from collected headlines.
6. Deliver the digest to Telegram on Sunday.

The automatic digest includes publisher attribution and original article links. It identifies source-reported news and does not claim that every headline has been independently verified.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A["GitHub Actions<br/>Daily Scheduler"] --> B["Configured RSS News Sources"]
    B --> C["Python RSS Collector"]
    C --> D["Data Normalization"]
    D --> E["Freshness and Relevance Classification"]
    E --> F[("Neon PostgreSQL")]

    E -.-> G["Optional Gemini AI<br/>Movie Information Extraction"]
    G -.-> F

    F --> H["GitHub Actions<br/>Sunday Scheduler"]
    H --> I["Weekly Digest Generator"]
    I --> J["Telegram Bot API"]
    J --> K["Weekly Kannada Movie News"]

    L["Health Monitor<br/>and Failure Alerts"] -.-> A
    L -.-> H
    L -.-> J
```

**Architecture notes:** Solid arrows represent the core collection and weekly delivery flow. Dashed arrows represent optional processing or supporting monitoring components.

The application uses scheduled GitHub Actions jobs rather than a continuously running application server.

---

## ✨ Key Features

### 1. Automated RSS Collection

The RSS collector retrieves article metadata from configured publisher feeds and processes updates incrementally.

- Collects news headlines, original URLs, and publication dates.
- Supports Kannada Unicode text.
- Filters stale articles.
- Prevents duplicate article insertion.
- Supports preview mode without database writes.

### 2. News Classification

A rule-based classification layer organizes incoming articles into:

| Classification | Meaning |
|---|---|
| `relevant` | Identified as relevant cinema news |
| `needs_review` | Potentially relevant but insufficient context |
| `not_relevant` | Classified as outside the target content |

The automatic weekly digest selects `relevant` and `needs_review` articles. This prioritizes receiving weekly updates over requiring independent factual verification.

### 3. AI-Assisted Movie Extraction

The project includes optional movie-information extraction using Google's Gemini API, Pydantic, and LangGraph-related components.

This functionality is separate from the regular RSS collection and automatic Telegram digest.

**Note:** AI extraction is implemented but requires appropriate API configuration and activation. The weekly digest does not depend on enabling it.

### 4. PostgreSQL Database

The system uses PostgreSQL with Neon cloud hosting.

The database maintains structured records for:

- News sources and collected articles.
- Classification and processing information.
- Movie candidates and supporting evidence.
- News events and review history.
- Telegram digest delivery tracking.
- Collection monitoring records.

Database uniqueness constraints help prevent duplicate records.

### 5. Automatic Telegram Digest

The weekly digest retrieves collected articles from the last completed Sunday–Saturday reporting period, formats them into a Telegram message, and includes links to the original publishers.

Manual approval is not required for the automatic digest workflow.

The system also tracks weekly delivery records to reduce duplicate Telegram sends.

### 6. Monitoring and Failure Alerts

The project includes cloud monitoring and notification components.

These support checks for unsuccessful workflows, collection activity, and Telegram delivery issues.

---

## 📱 Telegram Bot — Working Demonstration

The following screenshot shows a real Kannada Movie Radar Telegram delivery and a separately triggered failure-alert test.

![Kannada Movie Radar Telegram Bot](docs/images/telegram-digest.png)

*Figure 1: Actual Telegram bot demonstration showing a weekly Kannada film news digest and a test workflow-failure notification.*

The screenshot demonstrates a previously delivered, manually verified news digest for **November 1–7, 2026**. The current automatic digest implementation is a newer delivery path that sends source-reported headlines without requiring manual approval.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Main backend language |
| HTTPX | HTTP requests and feed retrieval |
| Feedparser | RSS and Atom feed parsing |
| PostgreSQL | Relational data storage |
| Neon | Managed cloud PostgreSQL |
| GitHub Actions | Scheduled cloud automation |
| Telegram Bot API | Weekly news delivery and alerts |
| Google Gemini API | Optional AI-powered movie extraction |
| Pydantic | Structured data validation |
| LangGraph | AI processing workflow components |
| Pytest | Automated testing |
| Ruff | Code linting and quality checks |
| Git & GitHub | Version control and source hosting |

---

## 📂 Project Structure

```text
kannada-movie-radar/
│
├── .github/
│   └── workflows/
│       ├── daily-collector.yml
│       ├── health-monitor.yml
│       └── sunday-digest.yml
│
├── docs/
│   └── images/
│       └── telegram-digest.png
│
├── migrations/
│   └── ... SQL database migrations
│
├── src/
│   └── radar/
│       ├── agents/
│       ├── collectors/
│       ├── database/
│       ├── services/
│       └── telegram/
│
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

---

## ⚙️ Installation and Local Setup

### Prerequisites

- Python 3.12
- Git
- PostgreSQL or a Neon PostgreSQL database
- A Telegram bot token and chat ID for delivery testing

### 1. Clone the Repository

```powershell
git clone https://github.com/Mounesh05/kannada-movie-radar.git
cd kannada-movie-radar
```

### 2. Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -e ".[dev]"
```

### 4. Configure PostgreSQL

Create a `.env` file in the project root.

For Neon:

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

Alternatively, configure a local PostgreSQL connection:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kannada_movie_radar
DB_USER=radar
DB_PASSWORD=your_password
```

Replace the example values with your own credentials.

Apply the SQL migrations in `migrations/` in numerical order before using a new database.

Verify connectivity:

```powershell
python -m radar.database.connection
```

Expected output:

```text
PostgreSQL connection successful!
```

---

## 🚀 Running the Application

### Preview RSS Collection

```powershell
python -m radar.collectors.pipeline --feed "https://www.cinisuddi.com/feed/" --dry-run
```

Preview mode prints article details without inserting records into PostgreSQL.

### Collect and Store Articles

For a feed you are authorized to ingest:

```powershell
python -m radar.collectors.pipeline --feed "https://www.cinisuddi.com/feed/"
```

This writes new eligible articles to the configured database and avoids duplicate URLs.

### Preview Weekly Telegram Digest

```powershell
python -m radar.telegram.automatic_digest
```

This displays the generated digest without sending a Telegram message.

### Send Weekly Digest

```powershell
python -m radar.telegram.automatic_digest --send
```

This sends the digest using the configured Telegram credentials. The system records delivery claims to prevent repeated sends for the same week and chat.

**Note:** The real send command should only be used with an appropriately configured Telegram bot and database.

---

## ☁️ Cloud Deployment and Scheduling

The project uses GitHub Actions for scheduled execution and Neon for persistent cloud storage.

| Workflow | Schedule (IST) | Purpose |
|---|---|---|
| Daily Collector | Every day, 8:00 AM | Fetch, classify, and store RSS articles |
| Health Monitor | Every day, 12:00 PM | Check pipeline health |
| Sunday Digest | Every Sunday, 9:00 AM | Deliver the previous week's collected headlines |

GitHub Actions schedules are configured in UTC and may experience execution delays.

### GitHub Actions Secrets

Configure these under **Repository Settings → Secrets and variables → Actions**.

| Secret | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `TELEGRAM_BOT_TOKEN` | Telegram bot authentication |
| `TELEGRAM_CHAT_ID` | Destination Telegram chat |
| `GEMINI_API_KEY` | Optional Gemini extraction |

Never commit these credentials to the repository.

### GitHub Actions Variables

| Variable | Purpose |
|---|---|
| `APPROVED_RSS_FEED` | Configured feed URL |
| `COLLECTION_ENABLED` | Enables scheduled article collection |
| `DIGEST_ENABLED` | Enables scheduled Sunday digest |
| `EXTRACTION_ENABLED` | Enables optional AI movie extraction |
| `GEMINI_MODEL` | Optional Gemini model selection |

Scheduled collection requires `COLLECTION_ENABLED=true` and an accessible, permitted feed.

The digest can operate independently of AI extraction.

---

## 🧪 Testing and Code Quality

The project uses Pytest for automated tests and Ruff for static linting.

Run the complete test suite:

```powershell
python -m pytest -q
```

Run lint checks:

```powershell
python -m ruff check src tests
```

The test suite covers various parts of RSS collection, normalization, classification, evidence handling, and application behavior.

A passing test suite validates covered software behavior; it does not by itself establish the accuracy of external news or the reliability of future scheduled executions.

---

## 🔐 Data Handling and Reliability

Kannada Movie Radar is designed around controlled data ingestion and transparent source attribution.

- Stores article metadata and references rather than republishing full publisher articles.
- Uses original article links in Telegram messages.
- Prevents duplicates using database constraints.
- Separates collected information from independent factual verification.
- Tracks weekly Telegram delivery attempts.
- Supports monitoring and failure notifications.
- Uses secret variables for database and API credentials.

The system should only perform recurring automated access to news sources under applicable access permissions and publisher conditions.

---

## 📊 Implementation Status

| Component | Status |
|---|---|
| RSS collection pipeline | Implemented |
| Classification and normalization | Implemented |
| PostgreSQL / Neon integration | Implemented |
| Duplicate prevention | Implemented |
| AI-assisted extraction | Implemented, optional |
| Evidence matching and review utilities | Implemented |
| GitHub Actions scheduling | Configured |
| Telegram bot delivery | Successfully demonstrated |
| Automatic weekly digest code | Implemented and connected to workflow |
| Recurring ingestion from third-party sources | Requires permitted feed access and enabled configuration |
| Fully unattended daily-to-Sunday production run | Not yet established by an end-to-end production test |

---

## 🎓 Academic Learning Outcomes

This project demonstrates practical experience in:

- Designing an automated data-ingestion pipeline.
- Working with Kannada-language Unicode data.
- Building modular Python backend services.
- Integrating relational databases with cloud infrastructure.
- Scheduling workloads using GitHub Actions.
- Designing duplicate prevention and delivery tracking.
- Integrating external APIs and AI processing tools.
- Applying automated testing and code-quality checks.
- Handling uncertainty and provenance in externally sourced information.

---

## 🔮 Possible Future Improvements

Potential enhancements include improved coverage of permitted Kannada cinema feeds, more precise title-based relevance classification, additional automated evaluations, and richer movie-level news grouping.

These enhancements are optional and are not required for the current automated weekly-news-delivery design.

---

## 👨‍💻 Author

**Mounesh**

GitHub: [github.com/Mounesh05](https://github.com/Mounesh05)

Repository: [Kannada Movie Radar](https://github.com/Mounesh05/kannada-movie-radar)

---

## 📄 License and Content Attribution

The project declares an MIT license in its Python package metadata.

News headlines, publisher content, logos, photographs, and linked articles remain subject to their respective owners' rights and applicable terms. The project's software license does not grant rights to third-party news content.

---

**Kannada Movie Radar — Collect Daily. Organize Automatically. Deliver Weekly.**