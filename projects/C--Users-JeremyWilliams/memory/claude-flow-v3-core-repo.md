---
name: claude-flow-v3-core-repo
description: New standalone repo repos\claude-flow-v3-core holds the v3 DDD core (foundation + task-management done 2026-07-17); 4 domains remain
metadata: 
  node_type: memory
  type: project
  originSessionId: 751f3f75-0179-4802-b904-e57f9ccb6c62
---

`C:\Users\JeremyWilliams\repos\claude-flow-v3-core` was created 2026-07-17 via `/v3-core-implementation`. User chose a **new standalone repo** (not the vendored upstream clone at `repos\ruflo-setup\ruflo\`) and scope **foundation + 1 domain**.

Done: shared kernel (immutable Entity/VO/AggregateRoot/DomainEvent, InMemoryEventBus, token-based DI — no inversify/decorators), task-management domain (immutable Task aggregate whose transitions return new instances, node:sqlite repository with `priority_rank` numeric ordering), AssignTaskUseCase (zod boundary validation, `Result<T,E>` returns). 79 tests, 98% coverage, 80% thresholds enforced. Local git only, no remote.

Remaining per skill blueprint: session-management, health-monitoring, lifecycle-management, event-coordination domains + microkernel. Follow the established patterns (immutability, typed errors, `.js` import extensions under NodeNext ESM, `types: ["node"]` in tsconfig).
