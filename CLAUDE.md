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
- **API-first, one logic layer.** The board's actual logic (querying/
  mutating `Company`/`Lead`) lives in one place — a real API, **Django
  REST Framework + `drf-spectacular`** for OpenAPI schema generation
  (chosen over Django Ninja: DRF is the resume-recognizable/mainstream
  choice for a portfolio piece; Ninja's built-in docs were the strongest
  case for it, but `drf-spectacular` closes that gap) — not duplicated
  between a `views.py` doing its own queries
  and a separate `api.py` doing the same thing again. The server-rendered
  templates are a thin consumer of that same layer, same as any other
  client (e.g. an agent like Claude Code reading board data later). This
  is a deliberate reaction to a real mistake seen elsewhere: letting a UI
  path and an API path drift into two independently-maintained
  implementations of the same logic. Keeping one logic layer means the
  still-undecided frontend question above stays genuinely open — swapping
  in htmx or a JS framework later is a rendering-layer change, not a
  backend rewrite.

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
- Cover-letter generation/drafting via an agent (e.g. Claude Code)
  consuming the board API — real goal, discuss and scope separately when
  picked back up, not blocking the current build.
- Rewriting the crawler in Go. Side-quest idea, not now.

## Architecture

Single project (`slayer/`), two apps, `django-environ` for env-var-backed
config (reads `.env` locally; real env vars in deployment).

- `board/models.py` — `Company`, `Lead` (status via `Lead.Status` choices).
- `board/services.py` — the one logic layer: `leads_by_status()`,
  `move_lead()`, `create_lead()`. Both `board/api.py` (DRF viewsets,
  mounted under `/api/`) and `board/views.py` (plain template views,
  mounted at `/`) call into this module instead of querying/mutating the
  models directly — that's the "one logic layer" piece from the scope
  notes above, made real.
- `board/templates/board/board.html` — the column-per-status kanban board,
  cards move via an ordinary form POST to `board:move_lead`.
- OpenAPI schema/docs via `drf-spectacular` at `/api/schema/` and
  `/api/docs/`.
- `crawler/models.py` — `WatchedCompany` (name, board token, comma-sep
  keyword filter), `ScrapedJob` (upserted by Greenhouse job id, links to a
  promoted `Lead` via `promoted_lead`).
- `crawler/management/commands/crawl_greenhouse.py` — fetches each active
  `WatchedCompany`'s board, upserts matching jobs, marks jobs no longer in
  the response as `is_active=False` (never deletes).
- `crawler/admin.py` — both models registered, plus a "Promote selected
  jobs to a Lead" admin action that calls `board.services.create_lead`.

Local dev DB is Postgres (`slayer_development`), created manually with
`createdb` — no seed data or fixtures ship in the repo per the no-real-data
rule above.

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
**Database: Postgres, decided.** Matches the pattern from the user's other
home-server project, `reef-1000`; no reason to reach for SQLite here.

Current state: scaffolded. `mise.toml` pins Python via the `latest` alias
(resolved to 3.14.7 at time of writing — Django 6.1 supports 3.12–3.14,
confirmed against Django's own compat table). `.venv` has Django +
dependencies installed, frozen to `requirements.txt`. Project and both
apps exist (`django-admin startproject` / `startapp` already run),
migrations committed, local Postgres dev DB created manually via
`createdb slayer_development`. Pushed to GitHub as `jonesdeini/slayer`
(public).

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
- Exact repo name/visibility timing on GitHub — when this actually gets
  pushed and flipped public.
- Whether/when to build a dedicated crawler review UI instead of relying on
  Django admin.
- API auth (token vs. none) — deferred, side-quest priority. Default
  assumption until revisited: trusted-network-only, same posture as
  `reef-1000`'s other services, no token required.
