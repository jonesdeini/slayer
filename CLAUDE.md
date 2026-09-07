# Slayer

A Django app to run an active job search: a kanban-style board to track
applications through a pipeline, plus a crawler that pulls fresh postings
from Greenhouse job boards so there's a queue of things worth looking at,
not just things already applied to.

**Name:** after Wheel of Time's Slayer (Isam/Luc) — a figure whose whole
deal is hunting people down. Seemed fitting for a job-hunt tool. Not a
security/offensive tool despite the name; don't let anyone mistake it for
one in the README.

Runners-up, rejected: "Wolfbrother" (Elyas's thing in the same series) —
turned out not to be unique to him, Perrin becomes one too, so it lost the
specificity that made it work. Elyas's actual individual wolf-name, "Long
Tooth," was considered once "wolfbrother" fell through — rejected as just
not as cool as Slayer.

## This repo is public — constraints that follow from that

This is a portfolio piece meant to be linked from a resume/cover letter, so:

- **Never commit real job-search data.** Which companies are being
  targeted, application statuses, interview notes, recruiter names — all of
  that is personal and stays in the local/deployed database only. No
  fixtures or seed migrations with real company names. If demo data is
  needed for a screenshot or a test, use obviously fake companies.
- **Same rule for the crawler's watch list.** Which companies' Greenhouse
  boards are being watched, and what keywords, reveals who's being targeted
  just as much as the kanban data does. Keep that out of committed
  fixtures/seed data too — config it locally (DB row or local-only file),
  not in the repo.
- **No secrets committed.** `SECRET_KEY`, DB credentials, anything
  env-shaped — via environment variables, with a `.env` that's gitignored
  and an `.env.example` carrying placeholder values only.

## Current scope

**Board app** — the kanban piece:
- `Company` and `Lead` (an application to a company for a role) models.
- Status pipeline: `NOT_STARTED`, `APPLIED`, `TECH_SCREEN`, `INTERVIEW`,
  `REJECTED` — the 5 the user asked for — plus `OFFER`, added as the
  natural terminal state alongside `REJECTED` (flagging this addition since
  it wasn't explicitly requested).
- **Frontend is explicitly not decided yet.** Build plain server-rendered
  Django views/templates first — a column-per-status board, moving a card
  between statuses via an ordinary HTML form POST. Do not reach for
  htmx/React/Vue/drag-and-drop (SortableJS etc.) unless the user
  specifically asks to commit to one — this was an explicit "not picking a
  front end yet unless I have to."

**Crawler app** — Greenhouse ingestion:
- Greenhouse only for v1 (explicitly out of scope: Lever and other ATSs,
  candidate for later, not now).
- Greenhouse exposes a public JSON API per company board token, no auth, no
  HTML scraping needed: `https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`.
- `WatchedCompany` (name, Greenhouse board token, keyword filters) +
  `ScrapedJob` (upserted from the API response, keyed by Greenhouse job id).
- A management command (`crawl_greenhouse`) does the fetch/filter/upsert;
  jobs no longer present in the API response get marked inactive rather
  than deleted.
- Review/promote flow: Django admin is the review queue for now (register
  both models, add a "promote to Lead" admin action) — deliberately not
  building a dedicated review UI yet, same "don't pick a frontend
  prematurely" reasoning as the board.

**Explicitly deferred, not in scope right now:**
- Importing the user's existing `leads.md` table (from his private
  `notes/job_hunt` tree) into this app's DB. Agreed this is real but too far
  ahead — don't do it until asked.
- Any drag-and-drop/JS-framework frontend decision.
- Lever/other ATS crawler support.

## Architecture

To be filled in as it's actually built. Two Django apps: `board` (kanban),
`crawler` (Greenhouse ingestion). Single project, single settings module,
env-var-backed config (`django-environ` or plain `os.environ` — TBD).

## Running locally

Python version is pinned per-project via `mise` (`mise.toml`, `[tools]
python = "..."`) rather than system Python (Arch's `pacman`-provided
Python) or a floating global default — keeps the interpreter reproducible
across machines without touching anything system-wide. Project
*dependencies* (Django, etc.) are a separate concern from the interpreter
pin: those still go through the standard `venv` + `pip` flow, not mise —
mise has a `pipx` backend for installing standalone global CLI tools, but
that's not the right fit for a project's own dependency graph.

Standard Django flow once scaffolded: `venv`, `pip install -r
requirements.txt`, `manage.py migrate`, `manage.py runserver`.
Database choice not locked yet — leaning Postgres (matching the pattern
from the user's other home-server project, `reef-1000`) over SQLite, but
this is a real open question, not decided.

Current state (as of scaffolding start): `mise.toml` pins Python via the
`latest` alias (resolved to 3.14.7 at time of writing — Django 6.1
supports 3.12–3.14, confirmed against Django's own compat table, so this
isn't the risky pick it might look like). `.venv` exists with Django
already `pip install`ed directly (not yet frozen to a `requirements.txt` —
that's a next step, along with actually running `django-admin
startproject`). Repo not yet `git init`'d as of this note.

## Deploying

Plan is to mirror the deploy pattern already proven on the user's home
server for `reef-1000` (see that repo's own `CLAUDE.md` for the full
reasoning) rather than invent something new:

- CI builds and pushes a Docker image to GHCR on merge to `main`, gated on
  tests/lint passing.
- A lightweight updater/poller service on the home server polls GHCR every
  ~5 min and recreates containers when the pulled image digest changes.
  Deliberately poll-based, not push-triggered — the box only ever reaches
  out (`docker pull`), no inbound port-forwarding or SSH access needed, no
  path for CI to execute anything on the box directly.
- The crawler runs as a scheduled management command via a small sidecar
  (cron or a loop+sleep container) — not Celery/Redis. Same "plain
  scheduled job over agent/heavy machinery" instinct as `reef-1000`'s own
  scope decisions: don't build more infra than a hobby-scale tool needs.

## Open decisions (don't assume an answer — ask or flag if it matters)

- Frontend approach for the board (plain templates vs. htmx vs. a JS
  framework) — unresolved on purpose.
- SQLite vs. Postgres for real.
- Exact repo name/visibility timing on GitHub — when this actually gets
  pushed and flipped public.
- Whether/when to build a dedicated crawler review UI instead of relying on
  Django admin.
