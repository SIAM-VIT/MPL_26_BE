# MPL Event Platform — Backend (MPL-BE)

FastAPI + SQLAlchemy (async) + PostgreSQL. Code judging: Judge0 CE
(with a local mock for development). Pairs with the **MPL-FE** repo,
which this API can serve at `/ui` for single-origin running (see §4).

If you read nothing else, read §2 (limitations) and §6 (Judge0 state).

---

## 1. Features

**Game core**

- Team login (`POST /api/auth/login`) returning a session token; each team's
  120-minute clock starts on its first login.
- MAIN arena API: list questions with starter code + visible samples
  (`GET /api/main/questions`), team clock (`GET /api/main/clock`), history
  (`GET /api/main/submissions`).
- **Run** (visible samples only, never scores) and **Submit** (all tests,
  awards partial credit) — one pipeline, synchronous end-to-end.
- Per-team, per-question progress tracking: best score, attempts, solve time.

**Judging & scoring**

- Two interchangeable judge backends behind one interface: local **mock**
  (no Docker) and real **Judge0 CE** — selected by `JUDGE_BACKEND`.
- Judge0 speaks the real protocol: base64 batch submit
  (`POST /submissions/batch`), token polling (`GET /submissions/batch`),
  per-test CPU/wall/memory limits, `X-Auth-Token` auth.
- Language IDs resolved **by name** from Judge0's `/languages` (exact match,
  then prefix match), with a hard-coded fallback table — never hard-coded
  as the primary source, because IDs differ between Judge0 versions.
- Four output comparators per question (`EXACT` / `TRIM` / `TOKENS` /
  `FLOAT`) — our comparator decides *correctness*, Judge0 decides *errors*.
- Weighted partial credit on the hidden pool, unlimited attempts, no
  negative marking, best-score-wins with improvement-only deltas.
- Judge failures never move scores: status 13 / timeouts / unreachable
  judge → verdict `ERROR`, score untouched, admin rejudges later.
- Hidden test inputs, answers — and even hidden stdout/stderr — are stored
  for admins but stripped from every team-facing response.

**Admin & ops**

- Full admin API under one passcode header: teams, questions, per-test-case
  CRUD, submissions browser, rejudge, leaderboard, add-time, judge health.
- `GET /api/admin/judge/health` reports backend, reachability, and the
  resolved language map — the event-day pre-flight check.
- Legacy challenge/bidding endpoints kept working for the boost/challenge
  pages (`challenge/create`, `assign-boost`, `review/mark-solved`).
- 65-step smoke suite (`tools/smoke_test.py`) covering login → run →
  submit → scoring → admin flows against a live server.
- Serves the frontend itself at `/ui` when pointed at a checkout
  (`FRONTEND_DIR`) — one process, one URL, no CORS on event day.

---

## 2. Limitations & known issues (read before the event)

### 🔴 Must verify or fix before event day

| # | Issue | Detail |
|---|---|---|
| 1 | **Judge0 client never talked to a real Judge0** | Written against the documented API; batch shape, polling, base64 and language IDs are plausible but **unproven**. §6 lists exactly what to prove. |
| 2 | **Only Python has ever been executed** | C / C++ / Java paths exist in both backends but never compiled or ran anywhere. |
| 3 | **Compose file is untested and version-skewed** | `docker-compose.judge0.yml` pins image `1.13.1` but configures it with the **pre-1.13 env-var style**; official 1.13.x configures via a mounted `judge0.conf`. Reconcile with the official compose before the event — as shipped, the stack may not boot. |
| 4 | **No load test** | Design target ~10 teams × 4 members; all testing was sequential. Judging is synchronous inside the HTTP request. |
| 5 | **FLOAT comparator quirk (verified)** | The float path compares the non-numeric "skeleton" *before* stripping trailing newlines, so `print(x)` output can fail against an otherwise equal expected value; only the TRIM fallback rescues byte-identical-after-trim text. Prefer `TRIM` for exact-output questions; test every `FLOAT` question with real submissions. |
| 6 | **Rejudge never claws back** | Rejudge computes `max(old best, new score)` — if a fixed test *lowers* a score, the team keeps the inflated points. Also recompute expectations manually after fixing a broken test. |

### 🟡 Accepted for Round 1 (by design or deferred)

- **One live session per team.** Login re-issues the team's single
  `session_token`, so a second device logging in invalidates the first.
  One team password + many laptops needs a session table (planned).
- **No global event controls.** No admin start/pause/resume/end; each team's
  clock runs from its own first login and a pause cannot freeze clocks.
- **Admin question PATCH is unvalidated** — it accepts any JSON field, and a
  bad `compare_mode` value bricks that question (500s) until fixed in the DB.
  Double-check every PATCH; never script it blindly.
- **Add-time is positive-only** with no reason field — time can be granted
  but not deducted, so bid prices/penalties need manual DB edits.
- **Legacy IDOR remains**: `GET /api/teams/{id}/status` and
  `/time-remaining` take a raw team id with no credential; the boost and
  challenge pages depend on them.
- **Leaderboard needs no credential** (convenient for the projector; the
  plan calls it admin-only — decide which you want).
- **No admin audit log** — clock changes and manual awards are not recorded
  anywhere. With ≤4 organisers this is tolerable; don't scale past it.
- **No database migrations** — schema changes mean `reset_db.py`
  (destructive; fine before the event, forbidden during it).
- **Cooldown is advisory under concurrency** — parallel submits in the same
  instant can all pass the 5 s gate (single serial submits are gated
  correctly). Runs are not cooldown-gated at all.
- **Teams start at 1000 points** (legacy default) rather than 0 — totals
  include it; change the default if you want clean standings.
- **No rate limiting** beyond the submit cooldown; **no plagiarism
  detection**; SQLAlchemy `echo=True` logs every statement (disable for
  quieter, faster event logs); default secrets ship in `config.py`
  (rotate `ADMIN_PASSCODE` and the DB URL via `.env`).

---

## 3. Run on Windows (local dev)

You need: **Python 3.11+** (python.org, tick "Add to PATH") and **Git**.
No Docker, no Postgres, no Node.

```powershell
# 1. clone + environment (first time only)
cd D:\projects
git clone <this-repo-url> MPL-BE
git clone <frontend-repo-url> MPL-FE
cd MPL-BE
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

```powershell
# 2. point .env at SQLite + the sibling frontend (one edit each)
#    DATABASE_URL=sqlite+aiosqlite:///./mpl.db   (comment out the postgres line)
#    FRONTEND_DIR=../MPL-FE
notepad .env
```

```powershell
# 3. database tables (first time only; DESTRUCTIVE — never during an event)
python reset_db.py

# 4. start the API (keep this window open)
uvicorn app.main:app --port 8000
```

```powershell
# 5. seed demo data — SECOND window, venv activated, server running
cd D:\projects\MPL-BE
.venv\Scripts\activate
python seed.py            # 3 demo teams + 3 demo questions (via the admin API)
```

Open `http://localhost:8000/ui/landing.html` → Log In → hub. Daily restart
is just step 4 (data persists in `mpl.db`).

**Logins:** Team Alpha / `alpha123`, Team Beta / `beta123`,
Team Gamma / `gamma123`. Admin passcode: `admin123`.

**Health checks:** `/` (service info) · `/health` (`{"status":"ok"}`) ·
`/docs` (interactive API docs) · `/api/admin/judge/health` (judge status).

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError` inside `(.venv)` | Deps installed into the wrong Python, or venv copied from another folder (venvs hardcode paths and break when moved) | Fresh venv: `deactivate; Remove-Item -Recurse -Force .venv; python -m venv .venv`, then `python -m pip install -r requirements.txt` |
| `Defaulting to user installation…` while venv is active | `pip` is not operating on the venv at all | Same fix; always use `python -m pip`, never bare `pip` |
| `seed.py` → connection error | Server not running | Start step 4 first; `seed.py` talks HTTP to `localhost:8000` |
| Port 8000 busy | — | Don't change ports (the frontend assumes 8000); kill the other process |
| `curl` examples fail in PowerShell | Quoting | Use the exact backtick-continued forms in §10, or Git Bash |

---

## 4. Pairing with the frontend (MPL-FE)

`/ui` appears only when the API is pointed at a frontend checkout via
`FRONTEND_DIR` (empty = `./frontend`, the classic single-repo layout; a
missing folder means clean API-only mode — `/` still answers, `/ui/*`
404s, the API is unaffected).

- **Recommended:** sibling clones + `FRONTEND_DIR=../MPL-FE` (§3) — one
  process, one URL, no CORS.
- **Alternative:** serve MPL-FE separately (Live Server / `python -m
  http.server`) — the pages call `http://localhost:8000/api` automatically.
  Keep the API on port 8000.

---

## 5. Judge0 implementation — exactly how it works

### 5.1 The two backends

`app/services/judge/__init__.py::get_judge()` picks one implementation
(the choice is cached — restarting the API is required after changing it):

| | `mock` (dev) | `judge0` (event) |
|---|---|---|
| Runs where | Your machine, `subprocess` in a temp dir, **sequential** (`asyncio.to_thread`, one test at a time) | Judge0 CE sandbox, parallel workers |
| Python | Really executes (`python3`/`python`) with `timeout = cpu_time_limit` | Real sandbox |
| C / C++ / Java | `gcc` / `g++` / `javac` **if installed**, else status 13 with a message telling you to switch to Judge0 | Real sandbox |
| Safety | **NOT a sandbox** — runs untrusted code as you | Isolated (see §6 caveats) |
| Off switch | `MOCK_EXECUTE_PYTHON=false` → every job returns status 13 ("use judge0") | n/a |

Mock status mapping (mirrors Judge0): `SyntaxError`/`IndentationError` →
6 Compilation Error; non-zero exit → 11 NZEC; timeout → 5 TLE; stdout
compared **byte-exact** → 3 Accepted / 4 Wrong Answer (deliberately
unhelpful, so our tolerant comparator does the rescuing).

### 5.2 Submit pipeline (`app/services/judging.py` — synchronous in the request)

1. `require_running` — clock expired → 403, nothing runs.
2. Guards — question must be MAIN; language must be allowed; source ≤
   `MAX_SOURCE_BYTES` (64 KB); per-question submit cooldown
   (`SUBMIT_COOLDOWN_SECONDS`, 5 s).
3. Case selection — **Submit runs every test; Run runs visible samples
   only** (and 400s if a question has none).
4. One `JudgeJob` per test (source, stdin, expected, per-question or
   default CPU/wall/memory limits) → `judge.run_batch(jobs)`.
5. Judge unreachable (exception) → verdict `ERROR`, score 0, attempt
   recorded, team retries. Any outcome with **status 13** → verdict
   `ERROR`, **no score change**, message says an admin can rejudge.
6. Otherwise results are built, scored, and committed; the response
   carries per-test detail with hidden IO stripped.

### 5.3 The Judge0 wire protocol (`judge/client.py` + `judge/polling.py`)

- **Submit:** `POST {JUDGE0_URL}/submissions/batch?base64_encoded=true&wait=false`
  with `{"submissions": […]}` — one entry per test, all base64. Unresolved
  language → synthetic status-13 outcome, never sent.
- **Payload per test:** `language_id`, base64 `source_code`/`stdin`/
  `expected_output`, `cpu_time_limit`, `wall_time_limit`, `memory_limit`,
  `redirect_stderr_to_stdout: false`, plus `X-Auth-Token` when configured.
- **Poll:** `GET /submissions/batch?tokens=…&base64_encoded=true&fields=token,
  status,stdout,stderr,compile_output,time,memory,message` every
  `JUDGE0_POLL_INTERVAL` (0.4 s) until no token is in status 1/2, or
  `JUDGE0_TIMEOUT_SECONDS` (30 s) elapses → remaining tests become
  status 13 "Judge0 polling timed out."
- **Languages:** `ensure_languages()` GETs `/languages`, matches our
  configured names exactly, then by prefix (`"Python (3"`), then falls
  back to the hard-coded ID table. Cached per process.
- **Health:** `GET /about` → 200. Surfaced with the resolved map at
  `GET /api/admin/judge/health` (admin passcode required).

### 5.4 Who decides what (status → pass/fail → verdict)

Judge0 is authoritative for **errors**; our comparator is authoritative
for **correctness**:

| Judge status | Meaning | Can the test pass? |
|---|---|---|
| 3 Accepted | ran fine | Yes — if `outputs_match()` says so |
| 4 Wrong Answer | ran fine, bytes differ | Yes — same comparator (rescues floats/whitespace) |
| 5 TLE, 6 Compile Error, 7–12 Runtime, 14 Exec Format | error | **No**, ever |
| 13 Internal Error | judge-side failure | **No** — and the whole submission becomes `ERROR` with **zero score change** |
| 1/2 still pending at timeout | overload/slowness | Converted to 13 (see §5.3) |

A compile error (6) is propagated onto every test's `compile_output` so
the team sees it once, clearly.

**Comparators** (`scoring.py`, per-question `compare_mode`, default `TRIM`):

| Mode | Rule |
|---|---|
| `EXACT` | byte equality |
| `TRIM` | strip trailing spaces per line + drop trailing blank lines, then compare |
| `TOKENS` | collapse all whitespace runs to single spaces, then compare |
| `FLOAT` | same count of numbers **and** identical non-numeric skeleton **and** each pair `math.isclose(rel=1e-6, abs=1e-9)`; if that fails, falls back to TRIM equality |

**Scoring:** `score = round(points × passed_hidden_weight /
total_hidden_weight)`; if a question has no hidden tests the pool is all
tests. Reported pass counts cover every test that ran. Team's question
score = best across attempts; only the improvement delta is added; Run
submissions always store 0.

**Verdicts:** all passed → `PASSED`; some → `PARTIAL`; none → `FAILED`;
zero tests ran → `FAILED`; any status 13 → `ERROR`.

### 5.5 Rejudge (`POST /api/admin/submissions/{id}/rejudge`)

Re-runs the stored source through the current judge + tests and updates
that submission. Two honest caveats (see §2.6): best score is
`max(old, new)` so fixed tests can't claw back points, and a rejudge that
hits a judge error still writes its partial score — recheck
`error_message` before trusting a rejudged row.

---

## 6. Judge0 current state — what is proven vs not

| Piece | State |
|---|---|
| Mock end-to-end (submit → execute → compare → score → leaderboard) | ✅ Proven (SQLite + Postgres paths, 65-step suite green) |
| Comparators, partial credit, best-score, hidden-IO stripping | ✅ Proven against live API |
| Judge0 client wire code | ⚠️ **Written, never executed** — no Docker was available where it was built |
| Language-name resolution + fallback table | ⚠️ Unproven (depends on real `/languages` output) |
| C / C++ / Java execution | ❌ Never ran (mock or Judge0) |
| `docker-compose.judge0.yml` | ❌ Untested **and** version-skewed (pre-1.13 env style vs pinned 1.13.1 image — reconcile with the official compose; expect a `judge0.conf` file) |
| Sandbox hardening (network-off, resource caps) | ❌ Not configured anywhere — the client sends no `enable_network=false`; verify in the Judge0 config you ship |

**Before event day, prove this list in order** (all on the real stack):

1. `docker compose -f docker-compose.judge0.yml up -d` → `/languages` answers.
2. `GET /api/admin/judge/health` → `healthy: true` **with all four IDs**.
3. Submit a known-good solution in **Python, C, C++ and Java** → all `PASSED`.
4. Submit a known-TLE + a compile error → statuses 5 and 6 surface correctly.
5. Rehearse 3–4 people submitting at once; watch for polling timeouts.

### Event-day Judge0 setup (condensed)

```powershell
cd D:\projects\MPL-BE
docker compose -f docker-compose.judge0.yml up -d
# wait 60–90 s for first-boot migration, then:
curl http://127.0.0.1:2358/languages        # JSON list = alive
```

```env
# .env
JUDGE_BACKEND=judge0
JUDGE0_URL=http://127.0.0.1:2358
JUDGE0_AUTH_TOKEN=<same value as AUTHN_TOKEN in the compose file>
MOCK_EXECUTE_PYTHON=false
```

Restart the API, re-run the 5 proofs above. Keep Judge0 on `127.0.0.1`
(never publish 2358 to the venue network), use image ≥ 1.13.1, and set a
real auth token even internally. Machine must never sleep. If Judge0 dies
mid-event: submissions return `ERROR` with no score change — fix it, then
rejudge the affected attempts.

---

## 7. API reference

### Team routes — require header `X-Team-Token` (returned by login)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | returns `session_token`; starts the clock on first login |
| GET | `/api/main/questions` | the 3 questions, visible tests, starter code, your best score |
| POST | `/api/main/run` | run against sample tests only — **never scores** |
| POST | `/api/main/submit` | run all tests, award partial credit |
| GET | `/api/main/submissions` | your own history |
| GET | `/api/main/clock` | your remaining time |
| GET | `/api/questions/{id}` | public question (no test cases) |
| GET | `/api/questions/{id}/sample-tests` | visible tests only |

### Admin routes — require header `admin-passcode`

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/admin/teams` | create team |
| GET | `/api/admin/teams` | list teams |
| POST | `/api/admin/teams/{id}/add-time` | add seconds (`id=0` = every team) |
| POST | `/api/admin/questions` | create question |
| PATCH | `/api/admin/questions/{id}` | edit any question field (**unvalidated** — see §2) |
| POST | `/api/admin/questions/{id}/test-cases?replace=true` | bulk-add test cases |
| GET | `/api/admin/questions/{id}/test-cases` | list (includes hidden) |
| DELETE | `/api/admin/test-cases/{id}` | delete one |
| GET | `/api/admin/submissions` | all submissions |
| GET | `/api/admin/submissions/{id}` | one submission + per-test detail |
| POST | `/api/admin/submissions/{id}/rejudge` | re-run and rescore |
| GET | `/api/admin/leaderboard` | standings (no auth) |
| GET | `/api/admin/judge/health` | backend + reachability + language map |

Legacy routes for the challenge/boost pages:
`POST /api/admin/challenge/create`, `POST /api/admin/teams/{id}/assign-boost`,
`POST /api/admin/review/mark-solved`.

---

## 8. Repository structure

```
app/                       backend package (≤200-line modules; see REFACTOR_NOTES.md)
  main.py                  app, CORS, /ui mount (FRONTEND_DIR), lifespan
  database.py              async engine, session factory, Base
  core/config.py           all settings, read from .env
  models/                  enums, team, question(+TestCase), progress,
                           submission, challenge — one module per aggregate
  schemas/                 questions, teams, submissions, admin (Pydantic)
  routes/                  auth · main (thin) · questions · teams (legacy) ·
                           admin/{deps,teams,questions,testcases,submissions,
                           leaderboard,legacy}
  services/
    judge/                 base DTOs · mock.py/execution.py (dev) ·
                           client.py + polling.py (Judge0 CE)
    judging.py             run/submit pipeline · scoring.py comparators+maths
    validation.py guards · access.py auth+clock · progress.py best-score ·
    results.py mapping · rejudge.py · arena.py / questions.py

seed.py + seeding/         demo data via the admin API
reset_db.py                drop + recreate all tables (dev only)
create_team.py             CLI: add one team
tools/smoke_test.py        65-step regression vs a live API (must exit 0)
REFACTOR_NOTES.md          module map · docker-compose.judge0.yml · docs/
```

| Table | Purpose |
|---|---|
| `teams` | name, passcode, `session_token`, points, `timer_start_time`, `extra_time_seconds` |
| `questions` | MAIN / TIME_BOOST / CHALLENGE; `sub_type`, `starter_code` (JSON/lang), `compare_mode`, `points`, limits |
| `test_cases` | per question: `stdin`, `expected_output`, `is_hidden`, `weight`, `position` |
| `team_question_states` | per team+question: `best_score`, `attempts`, status. Unique on (team_id, question_id) |
| `submissions` | one Run/Submit: source, language, verdict, score, `score_delta` |
| `submission_results` | per-test: status, stdout/stderr/compile output, hidden IO (admin-only) |
| `challenge_sessions` | legacy head-to-head (unused by MAIN) |

---

## 9. Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | postgres… | SQLAlchemy async URL (SQLite for dev, §3) |
| `ADMIN_PASSCODE` | `admin123` | **Change before the event** |
| `FRONTEND_DIR` | empty (`./frontend`) | folder served at `/ui`, e.g. `../MPL-FE` |
| `EVENT_DURATION_SECONDS` | `7200` | 120 minutes |
| `JUDGE_BACKEND` | `mock` | `mock` or `judge0` (restart after changing) |
| `JUDGE0_URL` | `http://judge0:2358` | Judge0 base URL |
| `JUDGE0_AUTH_TOKEN` | empty | `X-Auth-Token` sent to Judge0 |
| `JUDGE0_TIMEOUT_SECONDS` | `30` | hard cap for one full test batch |
| `JUDGE0_POLL_INTERVAL` | `0.4` | seconds between polls |
| `MOCK_EXECUTE_PYTHON` | `true` | **dev only** — really runs code locally |
| `DEFAULT_CPU_TIME_LIMIT` | `5` | s per test case |
| `DEFAULT_WALL_TIME_LIMIT` | `10` | s wall clock |
| `DEFAULT_MEMORY_LIMIT_KB` | `256000` | ~250 MB |
| `MAX_SOURCE_BYTES` | `64000` | source cap |
| `SUBMIT_COOLDOWN_SECONDS` | `5` | judge-queue guard, **not** an attempt limit |

---

## 10. Adding real questions

Use the admin API, not `seed.py` (PowerShell-safe quoting):

```powershell
# 1. create
curl -X POST http://localhost:8000/api/admin/questions `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '{"title":"Two Sum","description":"...","type":"MAIN","sub_type":"LEETCODE",
       "points":500,"compare_mode":"TRIM",
       "allowed_languages":"[\"python\",\"c\",\"cpp\",\"java\"]"}'

# 2. test cases — is_hidden:false shows as a sample in the editor
curl -X POST "http://localhost:8000/api/admin/questions/1/test-cases?replace=true" `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '[{"stdin":"4\n2 7 11 15\n9","expected_output":"0 1","is_hidden":false,"position":0},
       {"stdin":"3\n3 2 4\n6","expected_output":"1 2","is_hidden":true,"position":1}]'

# 3. starter code, one entry per language
curl -X PATCH http://localhost:8000/api/admin/questions/1 `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '{"starter_code":"{\"python\":\"n=int(input())\\n\",\"cpp\":\"#include <iostream>\\n\"}"}'
```

Guidelines: `FLOAT` for anything numeric (mind quirk §2.5 — test it);
always include ≥1 **visible** test; 3–5 hidden tests is plenty (each is a
sandbox run); starter code for all four languages; programs read stdin,
write stdout.

---

## 11. Working on this repo

`main` is stable; feature work on short branches, merged by PR after
`tools/smoke_test.py` exits 0 against a live server. Keep `app/` modules
small and single-purpose (`REFACTOR_NOTES.md`). Never commit a frontend
copy here — pair via `FRONTEND_DIR` (§4).
