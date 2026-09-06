Ты работаешь с неизвестной папкой, содержащей некоторый программный проект.

Это FORENSIC DISCOVERY / REPOSITORY BOOTSTRAP SESSION.

На старте ты НЕ знаешь:
- название продукта;
- назначение проекта;
- язык;
- архитектуру;
- build/runtime environment;
- является ли папка полноценным репозиторием;
- какие документы являются authoritative;
- какие файлы generated/vendor/cache;
- существуют ли submodules или внешние зависимости.

Не делай предположений на основании имени папки, README-заголовка или отдельных файлов.

Цель этой сессии: доказательно установить, что находится в папке, как это устроено, какие источники истины существуют и насколько проект готов к дальнейшему review или implementation.

## 0. Режим работы

Работа read-only.

Не изменяй:
- tracked files;
- Git refs;
- branches;
- tags;
- submodules;
- lockfiles;
- dependency state;
- generated artifacts;
- caches.

Не запускай destructive команды.

Не устанавливай зависимости, если это не требуется исключительно для безопасного чтения metadata.

Не считай утверждение доказанным только потому, что оно написано в README.

Разделяй:
- VERIFIED_SOURCE — непосредственно подтверждено содержимым файлов/Git metadata;
- EXECUTABLE_EVIDENCE — подтверждено реально выполненной проверкой;
- REVIEW_INFERENCE — логический вывод из нескольких verified facts;
- UNVERIFIED_EXTERNAL — зависит от внешнего repo/binary/service, который ещё не прочитан;
- UNKNOWN — данных недостаточно.

## 1. Сначала установить Git identity

Проверь:

- является ли папка Git worktree;
- repository root;
- current branch или detached HEAD;
- exact HEAD SHA;
- dirty/untracked state;
- remotes;
- upstream tracking;
- submodules и их exact gitlink SHA;
- nested repositories;
- worktrees;
- relevant tags.

Если это не Git repository, явно зафиксируй это и продолжай как filesystem/codebase discovery.

Не двигай refs.

## 2. Сделать inventory

Построй bounded inventory проекта.

Определи:

- количество файлов;
- top-level directories;
- языки;
- extensions;
- build/config files;
- package manifests;
- lockfiles;
- tests;
- CI workflows;
- scripts;
- docs;
- examples;
- generated/vendor/build/cache directories;
- binary artifacts;
- model/data assets;
- submodules/external source trees.

Отдельно классифицируй директории как:

SOURCE
TEST
DOCS
CONFIG
BUILD
GENERATED
VENDOR
CACHE
DATA/MODELS
UNKNOWN

Не включай vendor/generated/cache в архитектурные выводы без необходимости.

## 3. Найти authority documents

Ищи и прочитай, если существуют:

- README*
- AGENTS.md
- CONTRIBUTING*
- ARCHITECTURE*
- DESIGN*
- ADR/*
- docs/*
- ROADMAP*
- SECURITY*
- package/build manifests
- CI definitions
- deployment/runbooks
- environment files
- schema/contracts
- API specs

Составь таблицу:

document
claimed role
actual scope
freshness
authority confidence
conflicts

Если документы противоречат executable code/config, не выбирай победителя молча. Зафиксируй конфликт.

## 4. Определить executable structure

Установи:

- как проект собирается;
- как запускается;
- основные entrypoints;
- основные runtime components;
- process boundaries;
- network/API boundaries;
- storage/database dependencies;
- external services;
- model/runtime dependencies;
- CLI/TUI/UI/server components;
- deployment paths.

Для каждого компонента укажи evidence files.

Не объявляй компонент существующим только по названию директории.

## 5. Tests и CI

Найди:

- unit tests;
- integration tests;
- end-to-end tests;
- smoke tests;
- acceptance/gate scripts;
- CI workflows;
- lint/typecheck/static analysis.

Определи, какие проверки можно безопасно выполнить без изменения проекта.

Выполняй только безопасные проверки, для которых dependencies/environment уже доступны.

Никогда не пиши PASS, если проверка не была реально выполнена.

Разделяй:

PASS
FAIL
NOT RUN
BLOCKED
NOT APPLICABLE

## 6. External dependencies и submodules

Для каждого external repo/submodule/binary/service установи:

- имя;
- источник;
- exact revision/version, если доступен;
- зачем он нужен;
- является ли он source authority или только runtime dependency;
- включён ли он в текущий review scope.

Если submodule присутствует, его gitlink SHA является частью provenance.

Если внешний source tree не tracked/submodule и просто лежит рядом, пометь его UNTRACKED EXTERNAL и не смешивай его findings с parent repo.

## 7. CodeSleuth evidence

Если CodeSleuth доступен:

1. проверь существующие `.codesleuth/reports/` и индекс;
2. переиспользуй актуальный report только если его HEAD и scope совпадают;
3. создай/обнови repository inventory;
4. построй bounded RepositoryContextProjection;
5. сохраняй findings как durable evidence с file/blob references;
6. отличай verified graph edges от review inference;
7. не используй Mermaid или иной renderer как evidence authority.

Если существующий report относится к другому HEAD, явно пометь его predecessor/stale, но используй для history/delta analysis.

## 8. Найти архитектуру, но только после inventory

После этапов 1–7 сформируй architecture map:

COMPONENTS
ENTRYPOINTS
DATA FLOWS
CONTROL FLOWS
DEPENDENCIES
CONFIGURATION
EXTERNAL BOUNDARIES
TEST/GATE BOUNDARIES

Каждый важный узел или edge должен иметь evidence source.

Если архитектура неоднозначна, покажи competing interpretations вместо искусственного выбора.

## 9. Найти риски

Проведи bounded review минимум по категориям:

- correctness;
- portability;
- reproducibility;
- dependency/version coherence;
- supply-chain;
- unsafe path handling;
- config drift;
- state corruption;
- concurrency;
- error handling;
- observability;
- test coverage;
- documentation/code divergence;
- external dependency assumptions.

Не исправляй findings в этой сессии.

## 10. Итоговый отчёт

Верни отчёт со следующей структурой:

### Repository identity
- root
- branch
- exact HEAD
- dirty state
- remotes
- submodules

### What this project appears to be
Краткое описание, только на основании evidence.

### Confidence
HIGH / MEDIUM / LOW с объяснением.

### Inventory
Основные directories/files/classes of content.

### Authority map
Какие документы и executable artifacts являются источниками истины.

### Architecture
Компоненты и связи с evidence.

### Execution model
Build/run/deploy flow.

### Test and CI model
Что существует и что реально было запущено.

### External dependencies
Submodules/repos/binaries/services и их provenance.

### Findings
severity
location
evidence
impact
recommendation
confidence

### Unknowns
Что нельзя доказать из текущего checkout.

### Contradictions
Где docs/code/config расходятся.

### Recommended next session
Один из вариантов:
- implementation
- hardening
- test coverage
- dependency repair
- architecture investigation
- external dependency review
- no action required

## 11. Stop condition

Discovery считается завершённым только если можно ответить:

1. Что это за проект?
2. Как он запускается?
3. Где его основные source boundaries?
4. Что является authority?
5. Какие external dependencies существуют?
6. Какие tests/gates существуют?
7. Какие утверждения доказаны, а какие только inferred?
8. Достаточно ли evidence для безопасной implementation session?

Если хотя бы на один вопрос ответа нет, явно оставить его UNKNOWN, а не заполнять догадкой.
