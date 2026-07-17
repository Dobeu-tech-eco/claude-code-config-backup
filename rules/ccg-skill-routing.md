# CCG Domain Knowledge — Auto-routing Rules

When the user's request matches trigger keywords below, automatically READ the corresponding skill file to gain domain expertise before responding. These knowledge files are installed at `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/`.

**IMPORTANT**: Read the skill file FIRST, then respond. Do NOT fabricate domain knowledge from training data when a skill file exists.

## Security Domain (`domains/security/`) — NOT installed by default

> Security domain files contain red team/pentest reference content that may trigger antivirus false positives.
> They are NOT installed by default. To enable, manually copy from the npm package:
> `cp -r $(npm root -g)/ccg-workflow/templates/skills/domains/security/ C:/Users/JeremyWilliams/.claude/skills/ccg/domains/security/`

| Trigger Keywords | Skill File | Description |
|------------------|-----------|-------------|
| pentest, red team, exploit, C2, lateral movement, privilege escalation, evasion, persistence | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/security/red-team.md` | Red team attack techniques |
| blue team, alert, IOC, incident response, forensics, SIEM, EDR, containment | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/security/blue-team.md` | Blue team defense & incident response |
| web pentest, API security, OWASP, SQLi, XSS, SSRF, RCE, injection | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/security/pentest.md` | Web & API penetration testing |
| code audit, dangerous function, taint analysis, sink, source | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/security/code-audit.md` | Source code security audit |
| binary, reversing, PWN, fuzzing, stack overflow, heap overflow, ROP | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/security/vuln-research.md` | Vulnerability research & exploitation |
| OSINT, threat intelligence, threat modeling, ATT&CK, threat hunting | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/security/threat-intel.md` | Threat intelligence & OSINT |

## Architecture Domain (`domains/architecture/`)

| Trigger Keywords | Skill File |
|------------------|-----------|
| API design, REST, GraphQL, gRPC, endpoint, versioning | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/architecture/api-design.md` |
| caching, Redis, Memcached, cache invalidation, CDN | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/architecture/caching.md` |
| cloud native, Kubernetes, Docker, microservice, service mesh | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/architecture/cloud-native.md` |
| message queue, Kafka, RabbitMQ, event driven, pub/sub | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/architecture/message-queue.md` |
| security architecture, zero trust, defense in depth, IAM | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/architecture/security-arch.md` |

## AI / MLOps Domain (`domains/ai/`)

| Trigger Keywords | Skill File |
|------------------|-----------|
| RAG, retrieval augmented, vector database, embedding, chunking | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/ai/rag-system.md` |
| AI agent, tool use, function calling, agent framework, orchestration | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/ai/agent-dev.md` |
| LLM security, prompt injection, jailbreak, guardrail | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/ai/llm-security.md` |
| prompt engineering, model evaluation, benchmark, fine-tuning | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/ai/prompt-and-eval.md` |

## DevOps Domain (`domains/devops/`)

| Trigger Keywords | Skill File |
|------------------|-----------|
| Git workflow, branching strategy, trunk-based, GitFlow | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/devops/git-workflow.md` |
| testing strategy, unit test, integration test, e2e, test pyramid | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/devops/testing.md` |
| database, migration, schema design, indexing, query optimization | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/devops/database.md` |
| performance, profiling, load test, latency, throughput | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/devops/performance.md` |
| observability, logging, tracing, metrics, Prometheus, Grafana | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/devops/observability.md` |
| DevSecOps, CI security, SAST, DAST, supply chain | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/devops/devsecops.md` |
| cost optimization, cloud cost, FinOps, resource right-sizing | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/devops/cost-optimization.md` |

## Development Domain (`domains/development/`)

When the user is working with a specific programming language, read the corresponding skill file for language-specific best practices:

| Language | Skill File |
|----------|-----------|
| Python | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/development/python.md` |
| Go | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/development/go.md` |
| Rust | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/development/rust.md` |
| TypeScript / JavaScript | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/development/typescript.md` |
| Java / Kotlin | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/development/java.md` |
| C / C++ | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/development/cpp.md` |
| Shell / Bash | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/development/shell.md` |

## Frontend Design Domain (`domains/frontend-design/`)

| Trigger Keywords | Skill File |
|------------------|-----------|
| UI aesthetics, visual design, color theory, layout | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/ui-aesthetics.md` |
| UX principles, usability, user flow, information architecture | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/ux-principles.md` |
| component patterns, design system, atomic design | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/component-patterns.md` |
| state management, Redux, Zustand, Pinia, context | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/state-management.md` |
| frontend engineering, build tool, bundler, SSR, SSG | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/engineering.md` |
| claymorphism | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/claymorphism/SKILL.md` |
| glassmorphism | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/glassmorphism/SKILL.md` |
| liquid glass | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/liquid-glass/SKILL.md` |
| neubrutalism | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/frontend-design/neubrutalism/SKILL.md` |

## SEO Domain (`domains/seo/`)

| Trigger Keywords | Skill File |
|------------------|-----------|
| SEO, CTR, impressions, GSC, Search Console, keywords, seoTitle, meta description, internal linking, content strategy, blog translation, watermark removal SEO, 曝光, 点击率, 踩词, 优化标题, 搜索排名 | `C:/Users/JeremyWilliams/.claude/skills/ccg/domains/seo/seo-growth.md` |

## Routing Rules

1. **Keyword match is fuzzy** — match on intent, not exact string. "How to do SQL injection testing" triggers `pentest.md`.
2. **Multiple matches** — if a request spans two domains, read both skill files.
3. **Language detection** — automatically detect the programming language from file extensions or context, then read the corresponding development skill.
4. **Read once per conversation** — no need to re-read the same skill file within the same conversation.
5. **Skill files are authoritative** — when a skill file contradicts training data, the skill file wins.
