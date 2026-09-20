# AI Advisor Chatbot — Roko Šimpraga

## 1. Setup & run

**Prerequisites:** Docker and Docker Compose. Nothing else needs to be installed locally
— both the backend and frontend run inside containers.

1. Copy `backend/.env.example` to `backend/.env` and fill in a real OpenRouter API key:

   ```bash
   cp backend/.env.example backend/.env
   # then edit backend/.env and set OPENROUTER_API_KEY
   ```

2. From the repo root:

   ```bash
   docker compose up --build
   ```

3. Open **http://localhost:5173**.

The backend serves the API on `:8000` (health check at `/health`), the frontend dev
server on `:5173`. SQLite data lives in a named Docker volume (`sqlite_data`), so it
survives `docker compose down` (use `down -v` to reset to a clean database).

`OPENROUTER_MODEL` in `.env` is optional and defaults to `openai/gpt-4o-mini`.

## 2. Architecture overview

Two containers, wired by `docker-compose.yml` (the frontend's `depends_on` waits on the
backend's healthcheck so it never starts against a backend that isn't ready yet):

- **Backend** — FastAPI + SQLAlchemy 2.0 + SQLite (Python 3.12).
- **Frontend** — React 19 + TypeScript + Vite, TanStack Query v5 for all server state,
  react-router-dom v7, Tailwind v4.

```
Browser ──REST/JSON──> FastAPI ──tool-calling loop──> OpenRouter (openai/gpt-4o-mini)
                           │                                │
                           │                    ┌───────────┴───────────┐
                           │                real APIs:              app-state tools:
                           │           exchange rate / weather /   update_trip_plan /
                           │              public holidays          update_traveler_profile
                           ▼
                        SQLite
      conversations · messages · trip_plans · traveler_profile · system_prompt
```

**Backend layout** (`backend/app/`):
- `models.py` — `Conversation` → `Message`s and one `TripPlan` (1:1); `TravelerProfile`
  and `SystemPrompt` are singleton rows (id=1), since this is a single-user app.
- `routers/` — `conversations` (CRUD, trip-plan PATCH), `messages` (send a message, runs
  a full chat turn), `system_prompt` (GET/PUT the editable customization).
- `llm/chat.py` — the chat-turn orchestrator. Builds the context (optional user
  customization → conversation history → fixed `CORE_DIRECTIVE` → a "current state"
  block: a date lookup table, the traveler profile, the cross-conversation digest, this
  conversation's trip plan) and runs the tool-calling loop against OpenRouter (max 5
  iterations).
- `llm/tools.py` / `tool_impls.py` — 5 tools: three real external-API lookups
  (`get_exchange_rate` via Frankfurter, `get_weather` via Open-Meteo, `get_public_holidays`
  via date.nager.at — all free and keyless) plus two app-state tools
  (`update_trip_plan`, `update_traveler_profile`) bound to the current request's DB
  session via `functools.partial`.
- `core_directive.py` — the advisor's fixed, non-editable behavioral rules (stay in
  role, tool usage, honesty about unverifiable info, date resolution, trip-plan and
  traveler-profile discipline). Injected as its own system message, positioned *after*
  both the user's customization and the conversation history, so it always gets the
  strongest recency weighting and can't be diluted or overridden.
- `digest.py` — cross-conversation continuity: a compact digest of other conversations'
  trips (always in context) plus `find_duplicate_trip`, which detects an overlapping
  trip in another conversation for the UI's duplicate-trip notice.
- `conversation_title.py` — auto-titles a conversation from its first message, as a
  background task run after the reply is already sent, so it doesn't add latency.

**Frontend layout** (`frontend/src/`):
- `pages/` — `WelcomePage` (new chat + suggestions + splash), `ConversationPage` (chat
  rail + trip-plan panel side by side), `SettingsPage` (system-prompt editor).
- `components/` — `Sidebar` (list, rename, delete), `ChatRail` (messages + composer),
  `MessageBubble` (markdown via react-markdown + remark-gfm), `TripPlanPanel`
  (click-to-edit destination/dates/days), `DuplicateTripNotice`, `EditableText` (shared
  click-to-edit primitive), `SplashScreen`.
- All server state goes through TanStack Query; mutations invalidate the relevant
  queries so the sidebar, chat, and trip-plan panel stay in sync without a separate
  client-side store.

A chat turn: the frontend posts the message → backend persists it, builds the full
context, and loops on OpenRouter (running any requested tools) until a final text reply
→ persists that reply and returns it together with the (possibly updated) trip plan in
one response, so the UI doesn't need a second round-trip to refresh the plan.

## 3. Key decisions

- **Fixed `CORE_DIRECTIVE` + optional user customization, not one fully-editable system
  prompt.** The spec asks for both "stays in role" and "instructions are viewable and
  editable" — taken literally as one editable field, a traveler could edit away the
  role lock or tool rules. Split it: the advisor's actual behavior is hardcoded and
  always applied; the editable field (empty by default) can only add tone/style/extra
  rules on top, never remove core behavior.
- **SQLite over Postgres.** Single-user, no-auth, "one command on a clean machine" —
  SQLite in a named Docker volume gives real persistence with no extra service to
  orchestrate or fail to start.
- **A trip plan is 1:1 with a conversation**, not a separate top-level entity a
  conversation points to. Matches the spec's framing directly, and keeps plan ownership
  unambiguous — a traveler planning the same trip across two conversations gets a
  duplicate-trip nudge (see below) rather than a plan silently shared/merged between
  conversations. It seemed as a better solution to avoid model getting confused, still 
  the memory of the model stayed in shape in a way so it will remember previous trips and
  will take them into account.
- **Two-tier continuity.** Tier A: a passive digest of other conversations' trips is
  always in context, so the advisor can mention them in prose. Tier B: active duplicate
  detection (same destination, and overlapping dates when both sides have them) surfaces
  as a dismissible UI notice pointing at the other conversation. Considered silently
  merging trip data across conversations instead; rejected because a trip plan is
  explicitly scoped to one conversation and merging it behind the scenes would be
  surprising and hard to reason about.
- **`TravelerProfile` as its own durable-facts singleton**, separate from any one trip
  plan. Durable facts (home airport, dietary needs) need to outlive and sit outside any
  single trip, including a trip plan that later gets its conversation deleted.
- **Only real, keyless external APIs get a tool.** Exchange rates, weather, and public
  holidays all have solid free APIs, so `docker compose up` works with just an
  OpenRouter key. Deliberately did not build a visa/entry-requirements tool — there's no
  equivalent reliable free API — and instead made the advisor caveat that kind of answer
  as general knowledge rather than pretend it's verified. This also applies to other external
  information. It is shown in the project that free APIs can be implemented and if needed (and with
  the right resources) others can be added as well.
- **A deterministic date lookup table instead of asking the model to compute relative
  dates.** Testing showed the model reliably answers an isolated date question but
  miscalculates while simultaneously composing a multi-day tool call. Strengthening the
  prompt wording alone didn't fix it (see Known limitations/testing history in
  `PROMPTS.jsonl`); injecting a literal 21-day weekday→date table turns it from
  arithmetic into a lookup, which did fix it.
- **Auto-titling runs as a background task** using a small separate LLM call after the
  chat reply is already sent, so it never adds to the latency the user is waiting on.

## 4. Ambiguities

- **"Stays in role" vs. "instructions are editable."** These pull in different
  directions if taken as one field. Resolved with the fixed-directive/optional-
  customization split above.
- **How proactive should continuity be?** The spec says the advisor should "draw on"
  earlier conversations "when relevant" but doesn't say how far to take it. Chose two
  tiers (passive digest + active duplicate-trip nudge) rather than either doing nothing
  more than in-context mentions or silently merging data across conversations.
- **Is a trip plan one-per-conversation or one-per-trip?** Nothing in the spec rules
  either out. Chose one-per-conversation (simpler ownership, matches "a plan takes
  shape" as the conversation progresses) and used the duplicate-trip notice as the
  safety net for the case that creates.
- **Which "live" facts need a tool?** Visa requirements, exchange rates, and weather are
  all given as examples, not a required list. Built what has a free, reliable, keyless
  API (exchange rates, weather, holidays); for the rest (visas, opening hours, prices),
  made the advisor explicit that it's answering from general knowledge, not a live
  source.
- **"No login/accounts" vs. a traveler profile that persists "across conversations."**
  With no user concept at all, the traveler profile and system prompt are both single
  global rows — consistent with "no accounts," but means the app is single-user by
  construction, not just by default.

## 5. AI usage

Built entirely with Claude Code with minor interventions, in four phases (backend skeleton → conversation/
system-prompt CRUD → chat + tool-calling + continuity → frontend), each one scoped and
agreed in conversation before building it, rather than handing over the whole spec at
once. A few things beyond plain back-and-forth chatting:

- **Planning before building.** Each phase and sub-task was discussed and agreed first;
  a late-stage finishing plan (streaming → Tier B continuity → full testing → splash →
  polish → README) was proposed, discussed, and adjusted (SSE streaming explicitly
  evaluated and dropped after weighing the cost against the benefit for this app) before
  any of it was implemented.
- **Structured code review.** Phase 2, 3 and part of Phase 4 were reviewed using claude 
  skill for code review, agents gave great insight into bugs that were fixed afterwards.
  Big portion of the code was also reviewed by me (candidate). I questioned the files that
  Claude made and also added comments on what he should work on and what to fix.
- **Empirical verification, not just reading the diff.** A full pre-submission testing
  pass covered a genuinely clean-machine Docker startup (using an isolated, disposable
  Compose project so it wouldn't touch this repo's real dev data/volumes), a curl sweep
  of every API endpoint and all three external tools, and a live UI walkthrough
  (sidebar CRUD, trip-plan editing, the duplicate-trip notice, settings) driven through
  a browser tool.
- **Decisions stayed human-driven.** Architecture pivots were made by explicit instruction, with
  Claude proposing options and trade-offs rather than deciding unilaterally.
- Every prompt and a truncated copy of every response is logged to `PROMPTS.jsonl`
  (required by this assignment) — that log is the fullest record of how the app was
  actually built, turn by turn.

## 6. Known limitations

- **No streaming.** Replies arrive as one blocking response, not token-by-token. Looked
  at adding SSE, decided the cost didn't clearly pay off for this app's scale, and
  wrote it down rather than adding it half-heartedly.
- **Single-user by construction.** No accounts, no auth, no per-user data isolation —
  the traveler profile and system prompt are both global singleton rows. Correct per
  the spec's "no login, keep it simple," but it would need a real user concept before
  supporting more than one traveler.
- **No visa/entry-requirement tool.** The advisor caveats these answers instead of
  fetching them live, since there's no reliable free/keyless API for it. A production
  version would want a real data source here.
- **Traveler-profile and trip-plan "what's durable / what's a near-duplicate key"
  discipline is enforced only by LLM instruction-following**, not server-side — the
  model could still occasionally misfile a fact or create a near-duplicate key despite
  being told not to.
- **No automated test suite.** Verification in this build was manual (API sweeps + live
  browser walkthroughs, recorded in this session's history), not codified as
  regression tests — a real next step before ongoing changes.
- **No retry/backoff on external calls.** A flaky OpenRouter or tool-API response
  surfaces as a plain error rather than being retried.
- **CORS is wide open** (`allow_origins=["*"]`) — fine for a single-container-network,
  no-auth app; not something to carry into a real deployment.
- **SQLite** is the right call for this app's scope, not for real concurrent traffic.
- **`TripPlan.days` is a JSON blob**, not a normalized table — fine at this scale, would
  need to become a real relation if plans grew large or needed querying by day.

## 7. Beyond the spec

- **Duplicate-trip detection (Tier B continuity)** — proactively notices when a
  traveler is planning the same trip (destination + overlapping dates) in a different
  conversation and surfaces a dismissible notice linking to it, instead of only
  passively mentioning other trips in text.
- **Auto-titling** — conversations get a short, LLM-generated title from their first
  message, generated in the background so it doesn't cost reply latency.
- **A fully editable trip-plan panel** — click-to-edit destination, dates, and each
  day's title/activities, add/remove days, all server-validated (e.g. a day number
  outside the trip's date range is rejected with a clear message) — not just a
  read-only rendering of whatever the model last produced.
- **A general "be upfront about what you can't verify" rule**, not scoped narrowly to
  visas — applies to any topic the advisor answers from general knowledge rather than
  one of its three real tools.
- **Koalla** — a small branded identity (logo, "sleepy travel advisor" personality
  reinforced by the default placeholder in Settings, a waking-koala splash screen) on
  top of the functional requirements.
- **Markdown rendering** of assistant replies (react-markdown + remark-gfm) instead of
  plain text.
