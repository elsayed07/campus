# Architecture

## Background

Campus is a ground-up reconstruction of the e-learning project from a popular
Django tutorial. The original is organised by book chapter: a single fat
`courses` app holds subjects, courses, modules and polymorphic content via a
generic-relation `Content`/`ItemBase` hierarchy, with business logic living
inside class-based views and mixins, a DRF API bolted on, and chat logic embedded
directly in a Channels consumer. There are no real permissions beyond `is_staff`,
no progress tracking, payments, certificates, reviews, notifications, forums or
analytics, and no tests, Docker or CI.

This rebuild keeps the business domain but discards the chapter-driven structure
in favour of a domain-oriented, service-based architecture suitable for
production.

## Layering

Every app follows the same separation of concerns:

- **Models** define schema only.
- **Services** (`apps/*/services/`) own all writes and business rules. Views,
  consumers and API routers call services; they never embed logic.
- **Selectors** own reads and query optimisation (`select_related` /
  `prefetch_related`), returning N+1-free result sets.
- **Views / consumers / routers** are thin transport adapters.

Cross-cutting primitives live outside the apps:

- `shared/models` — `BaseModel = UUID + timestamps + soft delete`, inherited by
  every domain model. Analytics events are the exception: they are immutable, so
  they use `UUID + timestamps` without soft delete.
- `shared/exceptions` — typed domain errors (`ValidationError`, `ConflictError`,
  `NotFoundError`, `PermissionDeniedError`, `PaymentError`). The API maps these to
  HTTP status codes in one exception handler.
- `core/enums` — centralised choices. `core/permissions` — the RBAC layer
  (student / instructor / admin) enforced via mixins, decorators and service
  guards.

## Key design decisions

- **Single-table content** — `ContentItem` discriminates on a `kind` field rather
  than using the tutorial's generic-relation `ItemBase` hierarchy. This removes a
  layer of indirection and join complexity while keeping content polymorphic.
- **Pluggable progression** — `apps/progress/adaptive.py` defines a
  `ProgressionPolicy` protocol with `Open` and `Sequential` implementations,
  selected per course via `progression_mode`. New strategies (prerequisite graphs,
  mastery thresholds) can be added without touching the progress service.
- **Async side-effects on commit** — notifications, certificate rendering and
  analytics are dispatched inside `transaction.on_commit`, so they never fire for
  rolled-back transactions. Heavy work (PDF rendering, email) runs in Celery.
- **Payments isolation** — all Stripe SDK coupling lives in `apps/payments/gateway.py`.
  Webhooks are signature-verified, then handed to a pure `process_event` function
  operating on plain dicts, which makes the fulfilment logic trivially testable and
  idempotent.
- **Denormalised aggregates** — courses carry `rating_avg`, `rating_count` and
  `enrolled_count`; enrollments carry `progress_percent`. These are maintained by
  services to keep hot read paths cheap.

## Real time

`config/asgi.py` wires an `AuthMiddlewareStack` + `URLRouter` for WebSockets.
Two consumers exist: a per-user notification socket and a per-course chat socket.
Both are thin — chat delegates to `chat.services`, which enforces participation
(course owner or active enrollment), persists the message and broadcasts to the
course group on commit. Redis backs the channel layer.

## Data model (core relationships)

```
User ─< Course (owner)        Course ─< Module ─< Lesson ─< ContentItem
User ─< Enrollment >─ Course  Enrollment ─< LessonProgress >─ Lesson
Course ─< Review >─ User      Course ─< Thread ─< Post
Enrollment ─1 Certificate     User ─1 Subscription >─ Plan
User ─< Order >─ Course       Course ─< Event / CourseDailyStat
```

## Scaling considerations

- UUID primary keys avoid enumeration and ease future sharding/federation.
- Intentional indexes back the hot queries (course state + publish date, per-parent
  ordering, enrollment by student/status, event by course/kind/date).
- Selectors are query-count tested to prevent N+1 regressions.
- Redis serves caching (instructor overview), the Celery broker and the Channels
  layer; each uses a separate logical database.
- Analytics reads come from pre-aggregated `CourseDailyStat` rows produced by a
  nightly rollup, keeping dashboards cheap as event volume grows.
- The web tier is stateless (sessions and channels in Redis), so it scales
  horizontally behind nginx; Celery workers scale independently.
