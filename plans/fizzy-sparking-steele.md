# claude-flow v3 Core — Foundation + Task-Management Domain

## Context

The user invoked `/v3-core-implementation` (DDD core modules for claude-flow v3). No target existed: the only claude-flow v3 code on this machine is a vendored upstream clone (`repos\ruflo-setup\ruflo\`), and the home dir is config-only. **User confirmed:** build a **new standalone repo** at `C:\Users\JeremyWilliams\repos\claude-flow-v3-core`, scoped to **shared kernel + complete task-management domain + AssignTask use case, with tests** — proving the architecture before scaling to the other domains.

The skill blueprint is guidance, not gospel. It has defects we fix: mutating aggregates (violates the user's CRITICAL immutability rule), undefined `TaskResult`/`fromString`/Agent-repository references, a string-ordering bug in `ORDER BY priority`, and an inversify DI choice that breaks under esbuild/vitest (no `emitDecoratorMetadata`).

## Key decisions

| Decision | Choice | Why |
|---|---|---|
| DI | Hand-rolled token-based container (~100 loc) | inversify needs `emitDecoratorMetadata`, which esbuild (vitest) doesn't implement; zero deps, type-safe |
| SQLite | `node:sqlite` (`DatabaseSync`, built into Node 24) | No native build on Windows; `:memory:` for integration tests. Fallback: better-sqlite3 |
| Tests | vitest + `@vitest/coverage-v8`, 80% thresholds enforced in config | ESM-native, strict-TS-friendly |
| Modules | ESM, `NodeNext`; relative imports use `.js` extensions; **no** `paths` aliases | tsc doesn't rewrite aliases |
| Immutability | Every aggregate transition returns a **new** instance; events are a `readonly DomainEvent[]` ctor param; `clearDomainEvents()` returns a new instance | User rule overrides blueprint's `void`-mutation methods |
| Agent domain (out of scope) | `IAgentAvailability` port in application layer instead of Agent aggregate | Keeps use case honest without pulling in a second domain |
| Validation | zod only at boundaries: `AssignTaskCommand` parse + SQLite row parse. Domain VOs self-validate | User rule |
| Errors | `DomainError` hierarchy (`ValidationError`, `NotFoundError`, `InvalidTaskStateTransitionError`, `RepositoryError`, `UnexpectedError`); use case returns `Result<Success, Error>` union, never leaks raw errors | User rule |
| Priority ordering | Denormalized `priority_rank INTEGER` column; `findPendingTasks` orders by it | Fixes blueprint's `'high' < 'low'` string-sort bug |
| Cut from blueprint | `EntityCache` (incoherent with immutability), kernel dir, inversify | Out of scope |

## File tree

```
repos\claude-flow-v3-core\
├── package.json  tsconfig.json  tsconfig.build.json  vitest.config.ts  .gitignore  README.md
├── src\core\
│   ├── shared\
│   │   ├── domain\            domain-event.ts, value-object.ts, entity.ts, aggregate-root.ts, index.ts
│   │   ├── infrastructure\    event-bus.ts, dependency-container.ts, logger.ts, index.ts
│   │   └── types\             common.ts (Result), errors.ts, interfaces.ts (IClock), index.ts
│   ├── domains\task-management\
│   │   ├── entities\          task.entity.ts (create/reconstitute/assignTo/complete/clearDomainEvents)
│   │   ├── value-objects\     task-id.vo.ts, task-status.vo.ts, priority.vo.ts, task-result.vo.ts
│   │   ├── events\            task-assigned.event.ts, task-completed.event.ts
│   │   ├── services\          task-scheduling.service.ts (non-mutating sort)
│   │   └── repositories\      task.repository.ts (port), sqlite-task.repository.ts (+ initTaskManagementSchema)
│   └── application\
│       ├── ports\             agent-availability.port.ts
│       ├── commands\          assign-task.command.ts (zod)
│       ├── results\           assign-task.result.ts
│       └── use-cases\         assign-task.use-case.ts
└── tests\
    ├── unit\shared\           value-object, entity(+aggregate), event-bus, dependency-container, logger
    ├── unit\task-management\  4 VO tests, task.entity (immutability assertions), task-scheduling.service
    ├── unit\application\      assign-task.use-case (with fakes)
    ├── integration\           sqlite-task.repository.integration.test.ts (DatabaseSync ':memory:' per test)
    └── helpers\               fakes.ts (InMemoryTaskRepository, StubAgentAvailability, RecordingEventBus, FixedClock), builders.ts
```

All files <500 lines (largest ~180). No `console.*` outside `logger.ts`.

## Load-bearing contracts

```ts
// Entity: immutable, event-carrying
abstract class Entity<TId> { constructor(readonly id: TId, readonly domainEvents: readonly DomainEvent[]) }
abstract class AggregateRoot<TId> extends Entity<TId> { readonly version: number }

// Task transitions return NEW instances (version+1, events accumulated, frozen props)
class Task extends AggregateRoot<TaskId> {
  static create(description, priority, clock?): Task          // pending, version 0
  static reconstitute(props, version): Task                   // events: []
  assignTo(agentId, clock?): Task    // throws InvalidTaskStateTransitionError if completed/failed
  complete(result, clock?): Task     // throws if not assigned/in_progress
  clearDomainEvents(): Task
}

// TaskProps uses explicit `assignedAgentId: string | undefined` (exactOptionalPropertyTypes)

// Port stays async so the driver can be swapped later
interface ITaskRepository { save; findById; findByAgentId; findByStatus; findPendingTasks; delete }

// Use case flow: zod-parse → TaskId.fromString → findById (null→NotFoundError)
//   → agentAvailability.isAvailable (false→AgentUnavailableError) → task.assignTo()
//   → repo.save(next) → publish next.domainEvents (after persist) → ok(...)
// catch: DomainError → err(mapped); unknown → err(UnexpectedError) + logger.error
execute(input: unknown): Promise<Result<AssignTaskSuccess, AssignTaskError>>
```

SQLite schema: `tasks(id PK, description, priority, priority_rank, status, assigned_agent_id, created_at, updated_at, version)` + status index, via exported `initTaskManagementSchema(db)`.

## Build order

0. **Scaffold**: mkdir + `git init` + `.gitignore`; package.json (`"type":"module"`, scripts: build/typecheck/test/test:unit/test:integration/coverage); `npm i zod`, `npm i -D typescript @types/node vitest @vitest/coverage-v8`; tsconfig.json (ES2022, NodeNext, full strict incl. `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess` — **no** decorators, **no** paths); tsconfig.build.json (src only → dist, declarations); vitest.config.ts (v8 coverage, 80% thresholds, exclude `**/index.ts`); initial commit.
1. Shared types: common.ts (Result ok/err), errors.ts, interfaces.ts.
2. Shared domain primitives + unit tests (frozen props, equality, readonly events).
3. Shared infrastructure (logger, event-bus with per-handler error isolation, DI container) + tests.
4. Task VOs (TDD): TaskId (UUID validation), TaskStatus (+`canTransitionTo`), Priority (+`getNumericValue`), TaskResult (success/failure statics) + tests.
5. Domain events (thin).
6. Task aggregate + tests — must assert: original instance unchanged after `assignTo`; version increments; events accumulate across transitions; illegal transitions throw typed errors; `Object.isFrozen`.
7. TaskSchedulingService + tests (sort order, input array not mutated).
8. Repository port → SQLite impl → integration tests (`:memory:` per test): round-trip, upsert, priority ordering, corrupt-row → RepositoryError.
9. Application layer: port → zod command → result types → AssignTaskUseCase + unit tests (happy path, malformed input, not found, agent unavailable, illegal transition, repo failure → nothing published).
10. README, verify, final commit (conventional commits, no Co-Authored-By per user settings).

## Verification

```powershell
npm run typecheck    # zero errors under full strict flags
npm test             # unit + integration green
npm run coverage     # enforced ≥80% lines/functions/branches/statements
npm run build        # dist/ + declarations emit
node -e "import('./dist/core/application/index.js').then(m => process.stdout.write(Object.keys(m).join(',')))"
Select-String -Path src -Pattern 'console\.' -Recurse   # hits only logger.ts
```

Known friction: NodeNext requires `.js` on relative TS imports (typecheck catches misses); `node:sqlite` prints a one-time ExperimentalWarning (harmless).
