# CodeSleuth RC7 Competitive Integration Report

**Дата:** 2 сентября 2026
**Объект:** RC7 Consolidated Integration Architecture
**Фокус:** переносимость CodeSleuth на другие проекты и coding-agent hosts

## 1. Executive verdict

### Итог

**RC7 имеет конкурентный смысл, но не как ещё один coding agent.**

Если CodeSleuth попытается конкурировать с Cursor, Codex, Claude Code, GitHub Copilot или OpenHands в:

- agent loop;
- sandbox/runtime;
- tool routing;
- subagents;
- repository search;
- MCP;
- Skills;
- autonomous coding;

он проиграет просто по масштабу разработки.

Эти слои уже быстро commoditize.

Сильная позиция CodeSleuth находится **поверх них**:

> **host-neutral repository assurance layer: определить, что проект считает правильным, привязать это к exact commit, получить доказательства, не спутать неизвестность с PASS, провести bounded repair и доказать результат на новом exact subject.**

Именно сочетания

```text
repository-native authority
+ exact subject identity
+ immutable acceptance profile
+ durable evidence history
+ failed-subject immutability
+ bounded repair convergence
+ regression preservation
```

я не нашёл как целостного публично документированного продукта у рассмотренных конкурентов.

То есть moat есть. Но renderer zoo, собственный skill format, generic workflow engine и PKM-интеграции moat не являются.

---

# 2. Конкурентное поле

RC7 на самом деле конкурирует сразу с тремя классами систем.

### Coding-agent hosts

- OpenAI Codex
- Claude Code
- Cursor
- GitHub Copilot
- Continue
- OpenHands
- Aider

### Agent interoperability standards

- Agent Skills
- MCP
- частично host-native hooks / structured invocation APIs

### Engineering evidence / CI integration

- GitHub checks / code scanning
- SARIF
- обычные CI gate systems

Поэтому неправильный вопрос:

> «Кто конкурент CodeSleuth?»

Правильный:

> «Какие слои CodeSleuth уже стали commodity, а какой слой ещё не занят?»

---

# 3. Что рынок уже commoditized

## 3.1 Repository instructions

Это больше не конкурентное преимущество.

Codex использует `AGENTS.md`; OpenAI отдельно пишет, что монолитный огромный `AGENTS.md` оказался плохой моделью и что лучше держать короткую карту, ведущую к структурированной repository knowledge base.

GitHub Copilot поддерживает repository-wide, path-specific instructions, `AGENTS.md` и Agent Skills.

Cursor поддерживает Rules, `AGENTS.md`, Skills и project-specific review rules.

Claude Code имеет отдельные механизмы CLAUDE.md/rules/skills/subagents/hooks и разные уровни их загрузки и authority.

**Вывод:** документационная discipline CodeSleuth полезна, но не продаёт продукт сама по себе.

---

# 4. Agent Skills: здесь нельзя изобретать своё

Это одно из наиболее важных конкурентных изменений для CodeSleuth.

Agent Skills к 2026 году уже оформлен как открытый формат:

```text
skill/
  SKILL.md
  scripts/
  references/
  assets/
```

с progressive disclosure и portable semantics.

GitHub Copilot прямо заявляет поддержку Agent Skills open standard.

Cursor также называет Skills portable open standard и читает `.agents/skills`, `.cursor/skills`, а также compatibility directories Claude/Codex.

### Competitive consequence

CodeSleuth **не должен иметь свой competing Skill format**.

Правильная архитектура:

```text
CodeSleuth analytical competency
        ↓
Agent Skills compatible package
        ↓
OpenCode / Codex / Cursor / Claude / Copilot / …
```

При этом специфическим для CodeSleuth остаётся не упаковка Skill, а:

```text
evidence API
acceptance semantics
repair packet
durable state
```

Это существенно ускоряет переносимость продукта на другие проекты и hosts.

---

# 5. OpenAI Codex

## Что уже умеет конкурент

Codex:

- работает в изолированной среде;
- читает repository instructions;
- меняет код;
- выполняет тесты;
- выдаёт terminal/file citations;
- показывает test results;
- предоставляет проверяемую историю действий.

Внутри OpenAI вокруг Codex используются managed configuration, sandboxing, network policies и agent-native telemetry/audit logs.

Особенно интересен их «harness engineering» подход:

> repository knowledge становится system of record, а короткий `AGENTS.md` служит картой к глубокой документации.

Это практически независимо подтверждает правильность уже выбранной CodeSleuth discipline:

```text
short orientation
-> exact authoritative documents
-> bounded retrieval
```

### Где Codex сильнее

Codex намного сильнее как:

- execution runtime;
- sandbox;
- autonomous coder;
- long-running worker;
- infrastructure around agent runs.

### Где RC7 сильнее концептуально

Codex предоставляет **evidence of execution**.

RC7 пытается формализовать **engineering claimability**:

```text
какой exact subject?
под каким profile?
какие obligations?
какая evidence completeness?
что является UNKNOWN?
имеет ли PASS право переноситься?
```

Это другой слой.

### Threat level

**Medium as competitor, very high as host opportunity.**

Codex лучше рассматривать как один из идеальных execution hosts для CodeSleuth.

---

# 6. Claude Code

Claude Code уже предоставляет почти всё, что RC7 не должен реализовывать сам:

- permission modes;
- allow/deny tool rules;
- MCP;
- structured JSON / stream-json output;
- resumable sessions;
- `--max-turns`;
- hooks;
- project/enterprise policy hierarchy.

Особенно важен PreToolUse hook: host может детерминированно разрешать/запрещать tool invocation до исполнения.

### Competitive lesson

Это подтверждает решение из synthesis:

**Jinja не должен определять semantics исполнения.**

Правильнее:

```text
RepairPacket
    ↓
HostExecutionProfile
    ↓
validated native host actions/permissions
    ↓
Jinja = только presentation
```

Для Claude adapter CodeSleuth может компилировать constraints в:

```text
allowed tools
disallowed tools
permission mode
hooks
max turns
```

вместо того чтобы рассказывать модели в прозе «пожалуйста, не трогай это».

### Threat level

**Low direct / very high integration value.**

Claude Code конкурирует с host/runtime частью, которой CodeSleuth и не должен владеть.

---

# 7. Cursor: самый опасный функциональный конкурент

Из рассмотренных продуктов именно Cursor сейчас ближе всего подходит к части RC7 repair loop.

Bugbot:

- делает PR review;
- использует repository/team/learned rules;
- показывает, какие rules были использованы и какие были truncated;
- умеет MCP;
- может запускать Autofix;
- Autofix создаёт branch или пишет в PR branch;
- при записи в existing branch установлен предел **до трёх autofix attempts**, чтобы не получить бесконечный цикл.

Кроме того, локальный `/review-bugbot` сохраняет patch ID и синхронизирует его с удалённым PR review.

Cursor Cloud Agents также оставляют logs/screenshots/videos как proof artifacts выполнения.

### Это прямое подтверждение двух решений RC7

#### 1. Repair должен иметь deterministic bound

Рынок уже практически пришёл к:

```text
autofix != try forever
```

RC7 нужен более сильный вариант:

```text
max attempts
+ failure signature
+ obligation-state progression
+ oscillation detection
```

#### 2. Identity действительно нужна

Cursor использует patch identity для dedup/review synchronization.

CodeSleuth идёт сознательно строже:

```text
same patch/tree
but different Git SHA
!= same acceptance subject
```

Это не недостаток. Это именно assurance distinction.

### Где Cursor сильнее

- UX;
- distribution;
- autonomous implementation;
- review/fix integration;
- team rules;
- immediate Git provider integration.

### Где CodeSleuth может быть сильнее

Cursor Bugbot отвечает примерно:

> «Я просмотрел этот diff и вот мои findings.»

RC7 хочет отвечать:

> «Вот точный acceptance claim, его authority, exact SHA, profile digest, доказанные obligations, недоказанные obligations, failed history и новый repaired subject.»

Это существенно более сильная инженерная семантика.

### Threat level

**HIGH.**

Если RC7 repair loop останется лишь «agent reviews → agent fixes → tests», Cursor уже делает это лучше.

Если RC7 действительно реализует evidence/acceptance semantics, продукты перестают быть прямыми заменителями.

---

# 8. GitHub Copilot

Copilot code review сейчас умеет:

- repository instructions;
- `AGENTS.md`;
- Agent Skills;
- MCP context;
- автоматические reviews;
- source attribution для Skills/MCP в review comments;
- session logs с использованными tools;
- approval assessment.

В public preview Copilot approvals даже могут удовлетворять required approval rule репозитория, если это включено организацией.

### Очень важное конкурентное различие

GitHub может говорить:

```text
PR approved
```

CodeSleuth не должен конкурировать словом «approval».

Его claim:

```text
exact SHA S
under AcceptanceProfile P
has durable evidence E
for maturity/acceptance obligations O
```

Это намного уже и точнее.

### Где GitHub опасен

Distribution.

Если CodeSleuth требует большого нового UI/workflow, пользователь скорее нажмёт кнопку Copilot Review.

Поэтому CodeSleuth должен хорошо жить **внутри существующего GitHub workflow**, а не рядом с ним.

### Threat level

**HIGH on distribution, medium on semantics.**

---

# 9. Continue

Continue очень хорошо показывает, что host execution уже становится interchangeable infrastructure.

Он имеет:

```text
Chat
Plan
Agent
```

Plan mode предоставляет read-only инструменты, Agent mode добавляет mutation tools; MCP и rules подключаются отдельно.

### Competitive lesson

RC7 repair pipeline естественно раскладывается на:

```text
diagnosis      -> read-only
authorization  -> deterministic policy
mutation       -> host agent
verification   -> read-only/re-observation
```

Но CodeSleuth не должен создавать собственные Chat/Plan/Agent modes.

Adapter просто использует наиболее подходящий native mode host'а.

### Threat level

**LOW direct, medium ecosystem.**

---

# 10. OpenHands

OpenHands архитектурно почти является отрицательным примером того, чем CodeSleuth не должен становиться.

Его core включает:

```text
Agent
AgentController
State
EventStream
Runtime
Sandbox
Session
```

AgentController ведёт agent loop, EventStream является backbone событий, Runtime исполняет Actions и возвращает Observations.

Это полноценный agent platform.

### Competitive consequence

Если CodeSleuth создаст:

- собственный scheduler;
- controller;
- generalized event bus;
- generic runtime;
- workflow database;

то он начнёт конкурировать с OpenHands и одновременно нарушит собственный product contract.

### Правильная интеграция

```text
OpenHands owns AgentController/Runtime
          ↓
CodeSleuth exposes discipline/evidence contract
          ↓
OpenHands host executes RepairPacket
```

### Threat level

**LOW direct.**

Он подтверждает правильность отказа CodeSleuth от собственного runtime.

---

# 11. Aider

Aider давно использует concise repository map с важными symbols/signatures, чтобы дать модели контекст всей codebase.

Он также разделяет architect и editor roles.

### Competitive lesson

`RepositoryContextProjection` CodeSleuth не является уникальной идеей.

Но отличие принципиальное:

```text
Aider repo map
≈ useful model context

CodeSleuth RepositoryContextProjection
≈ bounded derived navigation with explicit source rehydration requirement
```

Именно evidence boundary является ценностью, не сам graph/map.

### Threat level

**LOW.**

---

# 12. Community signal: instruction fragmentation уже реальна

Даже Stack Overflow discussion показывает практическую путаницу между:

- `AGENTS.md`;
- Copilot instructions;
- path-specific instructions;
- tool-specific repository files.

Другие community discussions также приходят к идее одного canonical repository guidance source с pointer surfaces вместо нескольких расходящихся документов.

Это не normative evidence, но хороший market signal:

**CodeSleuth не должен добавлять ещё один обязательный proprietary instruction document.**

---

# 13. Competitive capability matrix

Оценка ниже означает **насколько feature является явно документированным core capability**, а не абсолютную техническую невозможность.

| Capability | RC7 target | Cursor | Copilot | Codex | Claude | Continue | OpenHands |
|---|---:|---:|---:|---:|---:|---:|---:|
| Agent execution | intentionally NO | ★★★ | ★★★ | ★★★ | ★★★ | ★★ | ★★★ |
| Cross-host Skills | ★★★ | ★★★ | ★★★ | ★★/★★★ | ★★★ | ★★ | ★ |
| MCP integration | ★★★ | ★★★ | ★★★ | ★★ | ★★★ | ★★★ | ★★ |
| Repo instructions | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ | ★★ |
| Repository context/map | ★★★ | ★★★ | ★★ | ★★★ | ★★ | ★★ | ★★ |
| Durable execution logs | ★★★ | ★★ | ★★ | ★★★ | ★★ | ★★ | ★★★ |
| Exact-SHA acceptance identity | **★★★** | ★ | ★★ | ★★ | ★ | ★ | ★ |
| Versioned acceptance profile | **★★★** | ★ | ★ | ★ | ★ | ★ | ★ |
| Non-binary claim semantics | **★★★** | ★ | ★ | ★★ | ★★ | ★ | ★ |
| Failed-subject immutability | **★★★** | ★ | ★ | ★ | ★ | ★ | ★ |
| Append-only engineering evidence | **★★★** | ★ | ★ | ★★ telemetry | ★★ logs | ★ | ★★ events |
| Bounded autofix/repair | **★★★** | ★★★ | ★★ | ★★ | ★★ | ★★ | ★★ |
| Deterministic no-progress stop | **★★★ target** | ★★ | ? | ? | max-turn bound | ? | ? |
| Protected regression memory | **★★★** | learned rules ★★ | instructions ★★ | repo docs ★★ | rules ★★ | rules ★★ | ★ |
| Authority vs projection distinction | **★★★** | ★ | ★ | ★ | ★ | ★ | ★ |
| Project maturity discovery | **★★★** | — | — | — | — | — | — |

Основной рисунок довольно очевиден:

**CodeSleuth проигрывает по execution и выигрывает только там, где остаётся assurance layer.**

---

# 14. Настоящий moat RC7

Из всего нынешнего design я бы выделил пять вещей, которые реально стоит защищать.

## Moat 1. Exact-head assurance

Не:

```text
agent says tests passed
```

а:

```text
SHA
+ exact profile
+ exact evidence
+ exact environment requirements
= bounded claim
```

Это гораздо ближе к engineering assurance, чем к AI chat.

---

## Moat 2. Acceptance profile identity

Очень сильная идея:

```text
same SHA
+ changed acceptance profile
!= same acceptance claim
```

У конкурентов широко распространены rules/instructions/configuration, но публичные workflows обычно не делают их identity полноценной частью acceptance proof.

---

## Moat 3. Unknown remains unknown

Agent products почти неизбежно оптимизируются на:

```text
task -> successful result
```

CodeSleuth может специализироваться на другом:

```text
PASS
FAIL
INCONCLUSIVE
UNAVAILABLE
NOT_APPLICABLE
```

При engineering use это ценнее, чем ещё немного agent autonomy.

---

## Moat 4. Repair that cannot rewrite history

```text
A failed
↓
A remains failed
↓
repair
↓
B
↓
new acceptance
```

Очень сильная и простая invariant.

Её надо сохранить практически любой ценой.

---

## Moat 5. Regression learning with explicit promotion

Cursor learned rules автоматически учатся по team behavior.

Это удобно, но CodeSleuth может занять более строгую нишу:

```text
observed failure
→ repair
→ regression witness
→ accepted repaired subject
→ preservation proposal
→ explicit promotion
```

То есть learning становится evidence-backed, а не просто statistical/team preference memory.

---

# 15. Где текущий RC7 всё ещё переусложнён

## 15.1 Renderer registry

Это не competitive moat.

JSON/Markdown/Jinja достаточно для core.

Mermaid оставить, потому что уже существует.

Вся остальная renderer галерея не делает CodeSleuth лучше против Cursor/Codex/Copilot.

**Срезать.**

---

## 15.2 Obsidian

Технически интересен.

Конкурентно почти не важен для RC7.

Он не помогает ответить:

> «Могу ли я завтра поставить CodeSleuth на Aleph, PII Parser или другой проект и безопасно им пользоваться?»

**После core.**

---

## 15.3 Generic Markdown importer

Не нужен.

Рынок явно движется в сторону standard Skills/rules/config formats, а не universal Markdown ETL.

**Убрать из критического пути.**

---

# 16. Где я бы НЕ согласился с последним synthesis

Есть один пункт, который я бы вернул раньше.

## SARIF

Review отправил SARIF далеко post-RC7 вместе с renderer zoo.

Для generic renderer architecture это правильно.

Но **маленький one-way Finding → SARIF adapter** имеет очень высокий интеграционный ROI.

SARIF является OASIS-standard форматом результатов анализа.

GitHub умеет принимать SARIF от сторонних анализаторов и показывать результаты в стандартном Code Scanning UI.

Поэтому я бы сделал:

```text
RC7 core
    ↓
small optional findings -> SARIF projection
```

Но только:

```text
Finding -> SARIF
```

Не:

```text
EHA -> SARIF
RepairCase -> SARIF
everything -> universal renderer
```

Это даст CodeSleuth дешёвую нативную интеграцию с существующим ecosystem.

### Recommendation

**SARIF = RC7 SHOULD / immediately-after-core**, а не большая post-RC7 feature family.

---

# 17. Что должно стать стандартным integration layer CodeSleuth

Я бы свёл portable integration architecture к четырём интерфейсам.

## 17.1 Agent Skills

Для reasoning procedures:

```text
authority-discovery
contract-triangulation
eha-evaluation
repair-diagnosis
```

Использовать open Agent Skills format.

---

## 17.2 MCP / native bounded tools

Для deterministic data:

```text
review_state
eha_state
implementation_state
repo_context
profile_state
```

Host вызывает их.

CodeSleuth не вызывает host model loop.

---

## 17.3 Host Execution Adapter

Очень тонкий:

```text
OpenCodeAdapter
CodexAdapter
ClaudeAdapter
CursorAdapter
ContinueAdapter
OpenHandsAdapter
```

Он знает только:

- как материализовать RepairPacket;
- как ограничить tools;
- как запустить host-native operation;
- как получить structured outcome;
- как остановить execution.

Он **не знает**, что означает PASS.

---

## 17.4 CI projection

```text
CodeSleuth evidence
    ↓
GitHub check
optional SARIF
human Markdown report
```

То есть пользователь остаётся в существующем workflow.

---

# 18. Минимальная конкурентоспособная вертикаль

Я бы теперь вообще оценивал RC7 по одному сценарию.

Возьмём абсолютно другой repository.

CodeSleuth должен суметь:

```text
1. Inspect repo

2. Discover:
   planning authority
   architecture authority
   build/test/release gates
   capability candidates

3. Produce:
   ProjectSibProfile proposal

4. Human adopts policy

5. Compile:
   immutable AcceptanceProfileSnapshot

6. Freeze:
   exact Git SHA

7. Run:
   acceptance through arbitrary supported host

8. Persist:
   durable evidence

9. Return:
   PASS / FAIL / INCONCLUSIVE / UNAVAILABLE

10. On FAIL:
    construct evidence-bound RepairPacket

11. Host repairs

12. Verify:
    actual diff
    scope
    regression witness
    gates

13. Produce new SHA

14. Run fresh acceptance

15. Preserve:
    failed A
    accepted B
    repair lineage
    regression obligation candidate
```

Если этот сценарий работает на:

```text
CodeSleuth
+
одном чужом небольшом repo
+
одном чужом сложном repo
```

RC7 практически доказал продуктовую гипотезу.

---

# 19. Что НЕ требуется для конкурентоспособности

До этого milestone не нужны:

- Obsidian;
- Canvas;
- GraphML;
- JSON-LD;
- universal renderers;
- generic Markdown importer;
- Doris;
- custom agent runtime;
- additional UI families;
- elaborate PKM;
- generalized workflow scheduler.

Это всё может быть хорошим продуктом.

Но не тем продуктом, который тебе сейчас нужен.

---

# 20. Самый опасный конкурентный риск

Он не называется Cursor.

Он называется:

> **complexity tax.**

У Codex/Cursor/Claude есть огромное преимущество:

```text
user asks
→ agent works
```

CodeSleuth добавляет:

```text
authority
profiles
evidence
claimability
repair lineage
integrity
```

Если пользователю ради этого надо понять двадцать новых nouns, продукт проиграет независимо от архитектурного качества.

Поэтому internal ontology может быть строгой, но внешний UX должен быть практически примитивным:

```text
codesleuth adopt
codesleuth check
codesleuth repair
codesleuth status
```

И всё.

Под капотом пусть живёт весь наш великолепный бюрократический аппарат.

---

# 21. Внешнее позиционирование

Не стоит продавать:

> Stable Integration Baseline Evidence-Based Context Epistemic Multi-Renderer Repair Framework.

Даже я бы сделал вид, что не увидел.

Лучшее позиционирование:

> **CodeSleuth makes coding-agent changes provable.**

Расширенная версия:

> **Use any coding agent. CodeSleuth discovers the repository's real engineering rules, proves an exact commit against them, and keeps failed and repaired evidence auditable.**

Или ещё точнее:

> **Your coding agent writes the code. CodeSleuth proves what happened.**

Это очень хорошо соответствует существующему architecture freeze:

```text
HOST owns execution
CodeSleuth owns discipline/evidence
```

---

# 22. Competitive priorities

## P0 — нужно сделать

1. Native Implementation Ledger.
2. EHA v2 profile-bound acceptance.
3. `ProjectSibProfile` adoption.
4. Immutable `AcceptanceProfileSnapshot`.
5. Non-binary outcomes.
6. Exact-SHA evidence.
7. Bounded repair.
8. Deterministic repair stop.
9. Regression witness.
10. Cross-host execution adapter contract.
11. Agent Skills compatibility.
12. MCP/bounded tool compatibility.

## P1 — сразу после working vertical

1. GitHub Check projection.
2. Finding → SARIF.
3. Claude adapter.
4. Codex adapter.
5. Cursor adapter.
6. Continue adapter.
7. External-host dogfood.

## P2

- richer graphs;
- additional renderers;
- Obsidian;
- PKM;
- analytics.

---

# 23. Final competitive assessment

### Product uniqueness

**Высокая**, если RC7 остаётся assurance layer.

### Execution differentiation

**Нулевая**, и такой она должна остаться.

### Ecosystem interoperability

Сейчас **средняя**, но может быстро стать высокой через Agent Skills + MCP + thin host adapters.

### Evidence / acceptance differentiation

**Очень высокая.**

### Repair-loop differentiation

**Средняя сегодня, высокая после deterministic/evidence-bound implementation.**

Cursor уже имеет bounded autofix. Поэтому просто auto-repair больше не уникален.

### Distribution disadvantage

**Большой.**

GitHub/Cursor/Codex/Claude уже находятся у пользователя.

Следовательно, CodeSleuth должен быть маленьким installable layer, а не отдельной средой разработки.

---

# 24. Recommendation

Продолжать RC7 стоит.

Но теперь у проекта должна быть почти жестокая product discipline:

```text
DO build:
proof
identity
authority
repair convergence
portability

DO reuse:
host runtime
Agent Skills
MCP
Git
CI
SARIF
existing agent permissions

DO NOT build:
another coding agent
another workflow engine
another knowledge platform
another graph platform
another universal serialization system
```

## Конкурентная формула продукта

```text
Cursor / Codex / Claude / Copilot / OpenHands
                =
              WORK

CodeSleuth
                =
       PROVE THAT WORK
```

Именно здесь у RC7 есть пространство, которое пока выглядит достаточно свободным и достаточно полезным, чтобы оправдать всё это писательское страдание.
