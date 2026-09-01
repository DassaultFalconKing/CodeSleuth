# 1. Executive verdict

## **DO NOT FREEZE RC7**

Я провёл review против exact head ветки `docs/rc7-ledger-authority-repair-plan`:

`befa2dd182b986bf56c3318bb578150f36c16e40`

Именно этот SHA сейчас является target ветки.  Техническое задание review взято из предоставленного handoff без переинтерпретации его цели. 

Причина вердикта не в том, что RC7 концептуально плох. Наоборот, несколько главных invariants сформулированы очень хорошо. Проблема хуже и интереснее: **план уже почти достаточно хорош, чтобы реализация могла уверенно закодировать оставшиеся неоднозначности как архитектурные факты**. Именно так и появляются вторые authorities, только уже с типами, digest'ами и прекрасной документацией.

Перед freeze остаются **четыре BLOCKER**, затрагивающих саму семантику EBCA:

1. `ProjectSibProfile` и `AcceptanceProfile` пока не имеют единственного недвусмысленного владельца acceptance truth.
2. Generic Ledger Repair пока допускает возникновение наддоменного authority для выбора «новой authoritative generation».
3. `REPAIR_LOOP_STALLED` описан семантически, но не определён детерминированно.
4. SIB0 completeness допускает опасное прочтение, будто human acceptance limitation может компенсировать неполноту evidence universe.

Все четыре должны быть закрыты **до** scope freeze.

Планирующий индекс сам говорит, что единый reviewed design ещё обязан разрешить profile identity, physical ledger schemas, repair generations, cross-ledger linkage, renderer registry, closure trust и прочее. Поэтому freeze сейчас противоречил бы даже собственному planning contract RC7.

### Evidence basis

| Документ                                    | Exact blob                                 |
| ------------------------------------------- | ------------------------------------------ |
| `RC7-PLANNING-INDEX.md`                     | `45515842872aafdc8f4bd7d00224e79bfe19b895` |
| `RC7-FEATURE-PLAN.md`                       | `ddac1c4a34b0c57f7c6ff668cc7e3d99a56f03c5` |
| `RC7-SIB-EHA-MATURITY-LOOPS.md`             | `47cb0f358c8043e7e83bb3f32e8586158372f0b9` |
| `RC7-REPAIR-PACKET-RENDERING.md`            | `21a63da327d21f79263d57b09c96eda0d8c28fe7` |
| `RC7-EBCA-GAP-PLAN.md`                      | `bbd30ef76be22e040ce320e2673eb0a58e16a3f3` |
| `RC7-STRUCTURED-OBJECT-MULTIRENDERER.md`    | `44f400f9ee7daeb11c48833bc5ac3a8e9951762c` |
| `RC7-CONTEXT-EPISTEMICS-DISPOSITION.md`     | `f1d632e9084d7c16ebbc1eb7572bcbaa59af58de` |
| `RC7-OBSIDIAN-ADAPTER-RESEARCH.md`          | `dcc5772b9f2ee8a61b394df0a3fcf83f36ab0cd0` |
| `EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md` | `232795994607b09016481846520b9c82554be5eb` |

Эти identities взяты непосредственно из GitHub contents responses для exact planning head.

---

# 2. Authority ownership table

Основной EBCA закон здесь прост: **authority является semantic ownership, а не удобным местом хранения**. Derived representation не может подняться вверх по цепочке просто потому, что её легче читать.

| Объект                              | Authoritative?                              | Что именно ему принадлежит                                       | Кто может писать                             | Главный риск                                                   |
| ----------------------------------- | ------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------- | -------------------------------------------------------------- |
| Git tracked source                  | **YES**                                     | exact repository bytes/object identities                         | project Git workflow / authorized host/human | никакой projection не должен исправлять его «по представлению» |
| `findings.ndjson`                   | **YES**                                     | original durable finding facts                                   | `review_state_record_finding`                | нельзя дублировать в generic claim ledger                      |
| `findings-amendments.ndjson`        | **YES, sibling authority**                  | lifecycle/correction history findings                            | domain amendment API                         | нельзя считать отдельной БД истины                             |
| planned Implementation Ledger       | **YES, new narrow authority**               | accepted-plan execution events                                   | bounded implementation-ledger API            | duplication gate/EHA facts                                     |
| `eha.ndjson`                        | **YES**                                     | campaign/verdict/repair history                                  | existing `eha_state` semantics               | RC7 не должен создать generic EHA ledger рядом                 |
| `protected-capabilities.json`       | **YES, registry authority**                 | contract lifecycle, dependency metadata, forbidden regressions   | explicit project contract process            | RepairLearning не должен создать второй negative ledger        |
| Development Authority Map           | **NO**                                      | derived evidence-bound interpretation/navigation                 | CodeSleuth tooling                           | `CONFIRMED` edge ошибочно принять за project canon             |
| `ProjectSibProfileV1`               | **AMBIGUOUS NOW**                           | должно быть либо adopted project policy, либо binding/read model | operator/project authority                   | первый BLOCKER                                                 |
| `AcceptanceProfileV1`               | **MUST NOT be independent authority**       | immutable acceptance snapshot                                    | generated/bound from one policy owner        | иначе дублирует ProjectSibProfile                              |
| `RepairCaseV1`                      | **NO**                                      | evidence-bound diagnosis package                                 | CodeSleuth derivation                        | не mutation permission                                         |
| `RepairPacketV1`                    | **NO**                                      | validated mutation constraints/instructions                      | CodeSleuth after policy validation           | не разрешает scope сам себе                                    |
| `RepairLearningRecordV1`            | **NO**                                      | derived post-repair lesson                                       | derived after fresh acceptance               | prose inference becoming canon                                 |
| `ClaimEnvelopeV1`                   | **NO**                                      | transport/read-model of EBCA dimensions                          | domain adapter                               | generic claim database by accident                             |
| ExternalEvidenceManifest            | **Evidence-only**                           | факт о recorded external observation                             | bounded ingestion tool                       | native PASS mistaken for EHA PASS                              |
| Ledger recovery manifest            | **provenance unless it selects generation** | corruption/recovery lineage                                      | domain recovery process                      | если выбирает authority generation, становится meta-authority  |
| generated Markdown                  | **NO**                                      | human presentation                                               | renderer                                     | Markdown write-back                                            |
| generic projected NDJSON            | **NO**                                      | serialized read model                                            | renderer                                     | путаница с authoritative NDJSON ledgers                        |
| Graphify                            | **NO**                                      | bounded semantic/navigation projection                           | renderer/query                               | missing edge interpreted as absence                            |
| Mermaid                             | **NO**                                      | presentation                                                     | renderer                                     | visual parity mistaken for semantic completeness               |
| Graphviz/GraphML                    | **NO**                                      | graph interchange/projection                                     | renderer                                     | graph subset loses non-graph meaning                           |
| JSON Canvas                         | **NO**                                      | spatial graph presentation                                       | renderer                                     | edited edges becoming lineage                                  |
| Obsidian Properties/Bases/backlinks | **NO**                                      | human knowledge/read model                                       | generated vault / user editing locally       | shadow authority                                               |
| Jinja rendering                     | **NO**                                      | host-facing wording                                              | trusted renderer/template                    | template policy drift                                          |
| SVG/HTML                            | **NO**                                      | final presentation                                               | renderer                                     | inherently one-way                                             |

Текущий durable-store contract уже делает правильное различие: findings, amendments и EHA находятся в одном узком evidence store, а projections/reports/Mermaid rebuildable и downstream-only. Он также прямо запрещает вторую durable authority для тех же фактов.

Отдельно хорошо, что существующий `ExternalEvidenceManifestV1` уже возвращает `authority: false` / `authority: "evidence-only"` и привязывает наблюдения к exact clean SHA и freshness TTL. Его `PASS` может быть нативным outcome внешнего check, но это **не EHA verdict**.

---

# 3. Findings by severity

## BLOCKER

### B1. `ProjectSibProfile` и `AcceptanceProfile` пока образуют потенциальную dual authority

`ProjectSibProfileV1` уже планируется хранить capability inventory, SIB obligations, native gates, required environments, candidate-selection authority, promotion/adjudication policy и прочее. Одновременно Gap Plan требует acceptance-profile identity и оставляет открытым, будет ли это часть `ProjectSibProfileV1` или отдельный `AcceptanceProfileV1`.

Это нельзя оставлять implementation choice.

Иначе возможна вполне честная с точки зрения кода, но ложная с точки зрения EBCA конструкция:

```text
ProjectSibProfile:
  SIB2 requires A+B+C

AcceptanceProfile:
  SIB2 requires A+B
```

Оба файла будут schema-valid. Оба с digest. И вот мы изобрели две истины, но зато с SHA256, чтобы ошибка выглядела солиднее.

**Required fix:** один владелец policy.

Рекомендованная модель:

```text
project-native authority
OR explicitly adopted ProjectSibProfile
                ↓
immutable AcceptanceProfileSnapshot
                ↓
EHA campaign
```

`AcceptanceProfileSnapshotV1` должен быть **compiled immutable snapshot**, а не independently editable authority.

---

### B2. Generic Ledger Repair пока может стать super-authority над domain ledgers

Feature Plan правильно запрещает rewriting history и требует immutable damaged bytes + predecessor digest + new recovered generation. Но одновременно оставляет generic surfaces вроде `ledger_repair_apply` и физическую схему выбора recovered generation на будущее.

Критический вопрос пока без ответа:

> Кто имеет semantic authority сказать, что generation B теперь canonical вместо generation A?

Если ответ: generic Ledger Repair layer, то он становится authority **над** findings, EHA и implementation ledgers. Это ровно тот generic super-ledger, который сам план запрещает.

**Required fix:**

```text
shared structural primitives
  parse / digest / detect corruption / lineage
                ↓
domain recovery policy
                ↓
domain-owned generation selection
```

Generic layer не должен иметь операцию вида:

```text
make_generation_authoritative(anyLedger)
```

Semantic amendment finding идёт через finding API. EHA через EHA domain. Implementation через implementation domain.

---

### B3. `REPAIR_LOOP_STALLED` не имеет детерминированной stopping semantics

Planning содержит хороший stop state и перечисляет:

* same failure topology;
* oscillation;
* no justified evidence increase.

Но это пока prose predicate.

Нет:

* automated-attempt budget;
* failure signature;
* state/diff fingerprint;
* oscillation detection;
* evidence-gain criterion;
* transition table.

То есть два агента могут бесконечно по-разному понимать «ещё есть шанс». Пользователь специально потребовал deterministic STOP. Сейчас его нет.

**До freeze определить**, например:

```text
AttemptIdentity =
  failedClaimId
  + targetSha
  + profileDigest
  + strategyId
  + diffDigest
  + focusedResultDigest
```

и детерминированные правила:

* same failure signature + no changed relevant evidence → STOP;
* A→B→A semantic/diff oscillation → STOP;
* host produced zero effective delta → STOP/host-postcondition failure;
* bounded automatic attempt count exceeded → STOP;
* repeated new patches without obligation-state improvement → STOP.

Конкретное число attempts может быть policy parameter, но отсутствие bound неприемлемо.

---

### B4. Human adjudication не может превратить incomplete universe в SIB0 completeness

Gap Plan правильно говорит, что discovery должен показывать universe, bounds, truncation и unread sources. Но фраза о том, что SIB0 proposal не claimable при uncontrolled universe **without explicit human acceptance of the limitation** создаёт опасную лазейку.

Это конфликтует с двумя более сильными contracts:

* EBCA: missing/truncated evidence remains unknown;
* SIB0: fundamental capability-class inventory должен быть complete/frozen.

Человек может сказать:

> «Да, мы принимаем этот bounded profile как policy.»

Но человек не может превратить:

> «мы не знаем, есть ли другие capability classes»

в:

> «мы доказали, что других нет».

**Required fix:** human adjudication может принять **scope**, но не доказать completeness.

Если completeness не supportable:

`SIB0 = INCONCLUSIVE / UNPROVEN`, не PASS.

---

## HIGH

### H1. Implementation Ledger рискует дублировать EHA gate truth

Feature Plan хочет писать в Implementation Ledger:

* gate/check execution evidence;
* verification result.

Но EHA ledger уже является authority для maturity verdict history.

Нужна жёсткая грань:

```text
Implementation Ledger:
"requirement R was worked on;
 verification run X was performed"

EHA Ledger:
"under profile P, exact SHA S received verdict V"
```

Если один gate участвует в EHA, Implementation Ledger должен хранить **reference to run/EHA event**, а не вторую independently authoritative копию результата.

---

### H2. `ClaimEnvelopeV1` слишком легко превращается в universal object of truth

План сам называет его non-authoritative transport/read-model. Это правильная оговорка.

Но наличие:

* `claimId`;
* generic `result`;
* authority refs;
* evidence refs;
* environment;
* cross-domain use;

создаёт слишком привлекательный объект для последующего `claims.ndjson`.

**Нельзя делать ClaimEnvelope persistent lifecycle domain.**

Лучше:

`EbcaClaimViewV1`

или shared interface, реализуемый domain objects:

```text
FindingClaimView
EhaVerdictClaimView
RepairDiagnosisClaimView
```

Owner-domain record остаётся truth source.

---

### H3. Generic Markdown ↔ NDJSON adapter для arbitrary repositories чрезмерен для RC7

Feature Plan требует configurable arbitrary-project codec с AST, frontmatter schema, identity extraction, ordering rules, unknown-field policy, migrations, walkthroughs и independent reuse.

Это уже не «починим implementation ledger».

Это начало самостоятельного data-mapping framework.

Хуже того, Markdown import создаёт потенциальный upstream path:

```text
edited Markdown
 -> parser
 -> domain records
 -> ?
```

**Перенести generic arbitrary-repository adapter в POST-RC7.**

RC7 максимум:

* authoritative ledger → generated Markdown;
* при необходимости один **explicit legacy-import proposal**:
  `Markdown -> candidate records -> validation/adjudication`, никогда direct authority write.

---

### H4. Multi-renderer scope уже превратился в маленький экспортный комбинат

Accepted planning перечисляет JSON, JSONC, YAML, TOML, JSON-LD, NDJSON, Markdown, HTML, Mermaid, DOT, GraphML, JSON Canvas, SVG, SARIF, JUnit XML, CSV и Jinja. Acceptance section даже требует canonical fixture через JSON/NDJSON/Markdown/Mermaid/DOT/Canvas/SVG.

Это противоречит заявленной scope restraint практически, хотя не логически.

RC7 нужен **renderer contract**, а не музей форматов.

Минимум RC7:

* JSON;
* authoritative/domain NDJSON там, где оно уже нужно;
* Markdown;
* Jinja host rendering;
* existing Mermaid, если это почти бесплатное сохранение нынешнего product surface.

Остальное POST-RC7.

---

### H5. Jinja не должен владеть даже semantic command construction

Repair rendering doc разрешает template управлять «host-specific command syntax».

Это слишком много.

Если Cursor template рендерит:

```text
run tests A B C
```

а Codex template:

```text
run tests A B
```

поле `verificationPlan` осталось одинаковым, но фактическое поведение уже разошлось.

Host/tool resolution должно жить в validated structured `HostExecutionProfile` или host adapter.

Jinja должен отвечать только за:

* wording;
* section order;
* escaping;
* presentation.

---

### H6. `closureTrust = DEGRADED` не имеет fail-closed consequence

Gap Plan запрещает narrow verification только для `UNTRUSTED`.

Что значит `DEGRADED`?

Если «можно использовать narrow closure с осторожностью», то это мягкая лазейка в false acceptance.

Нужно:

```text
TRUSTWORTHY -> narrow closure may be used
DEGRADED    -> deterministic conservative fallback
UNTRUSTED   -> full/wider verification or STOP
```

Причём fallback определяется acceptance policy, а не LLM.

Это особенно важно потому, что уже существующий `change_surface_state` использует эвристики по imports, filenames, token references, имеет bounds `5000 files / 200 entries / 512 KiB`. Он сам по конструкции не может обнаруживать весь dynamic/runtime dependency universe.

---

### H7. `RepairLearningRecord` не должен получить отдельный preservation authority

Planning здесь почти правильный: learning record заявлен derived-only.

Но он содержит `new preservation/negative obligation candidate`.

Existing normative contract уже назначил владельца:

`protected-capabilities.json -> contract.forbidden_regressions[]`.

Поэтому:

```text
RepairLearningRecord
   -> preservation proposal
   -> explicit project promotion
   -> existing protected capability registry
```

Никакого `repair-preservation.ndjson`.

---

### H8. Development Authority Map может случайно из discovery tool стать canon generator

Текущий implementation уже очень хорошо говорит:

> derived navigation, never replacement for repository-native authority.

Он привязывает relations к tracked blobs и имеет confidence `CONFIRMED | PROBABLE | UNPROVEN`.

Но будущий SIB bootstrap строит `ProjectSibProfile` именно из Development Authority Map.

Следовательно, необходимо записать:

> `DAM.CONFIRMED != project authority accepted`.

Это всего лишь conclusion supported by mapped evidence.

---

### H9. `NOT_APPLICABLE` требует более строгой анти-лазейки

План требует rationale. Хорошо.

Недостаточно.

`NOT_APPLICABLE` должен:

* применяться к конкретной obligation;
* иметь authority reference;
* не использоваться для обхода отсутствующей required environment;
* не делать сам SIB-level «неприменимым»;
* не превращать unavailable evidence в N/A;
* учитываться aggregation policy явно.

Иначе профиль можно сделать зелёным методом «ну этот Linux job, видимо, к нам духовно не относится».

---

### H10. RC7 EHA должен быть schema evolution существующего `eha.ndjson`, а не новым generic EHA store

Текущий `eha_state.ts` уже владеет:

* campaign identity;
* exact `targetSha`;
* SIB0/SIB1/SIB2 verdicts;
* cumulative claimability;
* repair lineage;
* durable completion.

Сейчас он поддерживает только `PASS|FAIL`, а `profile` является строкой.

RC7 должен **расширить этот authority**, добавив profile digest, environment/tool identities и non-binary outcomes.

Не создавать `generic-eha.ndjson` рядом.

---

## MEDIUM

### M1. `RepairCaseV1` нельзя использовать и для source repair, и для corrupted-ledger recovery

Это разные действия:

* source/EHA repair чинит новый Git subject;
* ledger structural recovery восстанавливает trustworthy history.

У них разные authorities и mutation permissions.

Разделить:

* `EhaRepairCaseV1`
* `LedgerRecoveryCaseV1`

---

### M2. Renderer registry лучше сделать static capability registry, не extension framework

Поля `acceptedSchemaIds`, loss profiles и capability declarations полезны.

Runtime plugin registry, arbitrary renderer loading и project-defined validation engines RC7 не нужны.

---

### M3. `RepairLearningRecord.rootCause` требует epistemic classification

`root cause` и `why previous checks missed it` часто являются **reasoned conclusions**, не direct observations.

Помечать как:

* observed;
* inferred;
* adjudicated;
* evidence refs;
* limitations.

Derived lesson не должен через красивую прозу превращать гипотезу в historical fact.

---

### M4. External evidence стоит ссылать, а не копировать

RepairPacket может содержать bounded excerpt для host convenience, но truth link должен оставаться на `ExternalEvidenceManifest` / source locator.

Иначе stale excerpt станет pseudo-authority.

---

### M5. Graph parity не означает semantic completeness

Graphify/Mermaid/DOT/Canvas могут согласиться между собой и одновременно потерять одно и то же поле.

Parity должна проверяться:

```text
domain object -> each renderer
```

а не только:

```text
renderer A == renderer B
```

---

### M6. Obsidian note body должен различать generated и user-owned space

Даже O1 projection пользователь сможет отредактировать физически.

Это нормально, пока regeneration semantics ясны.

Лучше:

```text
generated/
annotations/
```

или эквивалентный hard boundary, а не попытка магически сохранить смешанные machine/user sections.

---

## LOW

### L1. `ClaimEnvelope` слишком «канонически» звучит для non-authoritative view

`EbcaClaimViewV1` или `ClaimProjectionV1` меньше провоцирует будущее злоупотребление.

### L2. `DEGRADED_BUT_READABLE` и `DEGRADED` следует унифицировать

Иначе через несколько releases появится восхитительная таблица преобразования пяти разновидностей «почти доверяем».

---

# 4. PRAISE / STRONG DESIGN

Эти решения **не следует упрощать**:

1. **Failed SHA remains failed.** Repair создаёт новый subject и новую кампанию. Это полностью соответствует exact-head acceptance.
2. **Ancestry transfers context, never acceptance.** Сохранить буквально.
3. **Finding Ledger != Implementation Ledger != EHA Ledger.** Сохранить физически и семантически.
4. **Typed validated packet -> renderer -> host.** Очень сильная граница.
5. **Postcondition re-observation.** Host prose и exit code не становятся repository state.
6. **Source rehydration перед material mutation.** Graph/search/report остаются navigation.
7. **Obsidian pluginless-first / one-way.** Правильная архитектура для внешнего knowledge frontend.
8. **Context Epistemics split.** Generic Negative Claims, R0-R3, ROAP и long-context tests действительно должны оставаться потом.
9. **Regression witness -> preservation proposal -> explicit promotion.** Не автоматический canon.
10. **Host remains execution authority.** RC7 repair Playbook не должен приобрести собственного supervisor/runtime. Нормативный Playbook contract уже это запрещает.

---

# 5. RC7 / post-RC7 disposition

| Capability                                           | Disposition                                |
| ---------------------------------------------------- | ------------------------------------------ |
| Implementation Ledger                                | **RC7 MUST**                               |
| Extend existing EHA schema with profile/env/outcomes | **RC7 MUST**                               |
| Immutable AcceptanceProfile snapshot/digest          | **RC7 MUST**                               |
| ProjectSibProfile discovery + explicit adjudication  | **RC7 MUST**                               |
| Cross-ledger stable IDs                              | **RC7 MUST**                               |
| Domain-specific ledger integrity/recovery            | **RC7 MUST**                               |
| RepairCase / RepairPacket                            | **RC7 MUST**                               |
| deterministic repair stopping                        | **RC7 MUST**                               |
| rehydration + postcondition verification             | **RC7 MUST**                               |
| regression witness                                   | **RC7 MUST**                               |
| closure trust + completeness/truncation              | **RC7 MUST**                               |
| JSON / NDJSON / Markdown                             | **RC7 MUST**                               |
| Jinja host presentation                              | **RC7 MUST**                               |
| existing Mermaid integration                         | **RC7 SHOULD**                             |
| small read-only EBCA claim interface                 | **RC7 SHOULD**                             |
| RepairLearningRecord                                 | **RC7 SHOULD**                             |
| full generic renderer framework                      | **POST-RC7**                               |
| arbitrary Markdown↔NDJSON project codec              | **POST-RC7**                               |
| JSONC/YAML/TOML/JSON-LD general renderers            | **POST-RC7**                               |
| DOT/GraphML/JSON Canvas/SVG framework                | **POST-RC7**                               |
| SARIF/JUnit/CSV integrations                         | **POST-RC7**                               |
| Obsidian O1 product adapter                          | **POST-RC7**, RC7 research fixture at most |
| Obsidian import O2                                   | **POST-RC7**                               |
| Obsidian plugin O3                                   | **POST-RC7**                               |
| durable generic Negative Claims                      | **POST-RC7**                               |
| `FORBIDDEN_INFERENCE` graph                          | **POST-RC7**                               |
| universal R0-R3 mutation policy                      | **POST-RC7**                               |
| ROAP                                                 | **POST-RC7**                               |
| traceability completeness auditor                    | **POST-RC7**                               |
| long-context/grounding suite                         | **POST-RC7**                               |
| assurance-case/SACM projection                       | **POST-RC7**                               |
| authenticated attestations/SLSA-style extension      | **POST-RC7**                               |
| generic workflow engine                              | **REMOVE**                                 |
| generic claim database                               | **REMOVE**                                 |
| generic semantic super-ledger repair                 | **REMOVE**                                 |
| bidirectional Obsidian sync                          | **REMOVE from RC7**                        |

---

# 6. Adversarial failure-mode audit

Ниже 22 сценария, чтобы архитектура не прошла review исключительно потому, что все behaved politely.

|  # | Adversarial state                                         | Correct outcome                                                                |
| -: | --------------------------------------------------------- | ------------------------------------------------------------------------------ |
|  1 | test stale, code+authority agree                          | `TEST_AHEAD`; repair test only if authority established and scope permits      |
|  2 | docs stale, code+tests agree                              | repair docs only if normative authority resolves direction; otherwise operator |
|  3 | code/docs/tests contradict                                | `OPERATOR_DECISION_REQUIRED`                                                   |
|  4 | repair requires new capability class                      | `ARCHITECTURE_REOPEN_REQUIRED`                                                 |
|  5 | repair requires adjacent forbidden path                   | `SCOPE_EXPANSION_REQUIRED`                                                     |
|  6 | fix A causes protected regression B                       | focused/preservation FAIL; no candidate promotion                              |
|  7 | attempts alternate A↔B                                    | deterministic `REPAIR_LOOP_STALLED`                                            |
|  8 | host says fixed, worktree unchanged                       | postcondition failure; **no new candidate**                                    |
|  9 | host changes forbidden path                               | reject mutation result; scope stop                                             |
| 10 | RepairPacket source blob changed                          | `EVIDENCE_UNTRUSTED` / packet stale; regenerate                                |
| 11 | repair rationale exists only in Graphify summary          | rehydrate source or stop                                                       |
| 12 | live service unavailable                                  | `LIVE_EVIDENCE_REQUIRED` / `UNAVAILABLE`; never PASS                           |
| 13 | failure cannot be reproduced                              | `INCONCLUSIVE`; no speculative auto-repair                                     |
| 14 | deterministic regression witness cannot be produced       | operator decision or profile-approved equivalent witness                       |
| 15 | capability discovery truncated silently                   | profile invalid for SIB0                                                       |
| 16 | capability discovery visibly incomplete                   | SIB0 `INCONCLUSIVE/UNPROVEN`                                                   |
| 17 | dynamic/generated/runtime dependency missing from closure | `AFFECTED_CLOSURE_UNTRUSTED`; widen gate or stop                               |
| 18 | obligation incorrectly marked `NOT_APPLICABLE`            | profile validation failure; no campaign PASS                                   |
| 19 | same tree, different Git SHA                              | new acceptance subject; fresh EHA                                              |
| 20 | same SHA, changed profile digest                          | new acceptance claim; old PASS not claimable                                   |
| 21 | same SHA/profile but materially different tool/runtime    | profile-required evidence rerun or `UNAVAILABLE/INCONCLUSIVE`                  |
| 22 | finding→repair cross-link points to absent event          | lineage degraded/untrusted; never synthesize missing fact                      |

И ещё четыре особенно неприятных projection cases:

| Scenario                                                | Correct outcome                                     |
| ------------------------------------------------------- | --------------------------------------------------- |
| Markdown says PASS, EHA ledger says FAIL                | projection drift; regenerate Markdown; FAIL remains |
| Obsidian frontmatter manually changed `FAIL -> PASS`    | ignore as authority; vault is tampered derived view |
| Canvas edge changed to connect accepted SHA to old PASS | ignore; Canvas lineage has no write authority       |
| external evidence TTL expired                           | stale evidence; re-observe rather than reuse        |

---

# 7. Proposed types/interfaces: remove, merge, split, retain

| Proposed type                   | Verdict              | Required change                                                        |
| ------------------------------- | -------------------- | ---------------------------------------------------------------------- |
| `ClaimEnvelopeV1`               | **REDUCE**           | read-only EBCA view/interface; no persistence/lifecycle                |
| `RepairCaseV1`                  | **SPLIT**            | `EhaRepairCaseV1` vs `LedgerRecoveryCaseV1`                            |
| `RepairPacketV1`                | **RETAIN**           | explicitly host mutation packet, non-authority                         |
| `RepairLearningRecordV1`        | **RETAIN DERIVED**   | produced only after fresh acceptance                                   |
| `ProjectSibProfileV1`           | **RETAIN**           | explicit authority mode: adopted policy vs binding to native policy    |
| `AcceptanceProfileV1`           | **MERGE/REDUCE**     | immutable `AcceptanceProfileSnapshotV1`, never second policy authority |
| renderer registry               | **REDUCE**           | static internal capability descriptors in RC7                          |
| Markdown↔NDJSON generic profile | **POST-RC7**         | no arbitrary repo DSL now                                              |
| generic ledger validator        | **RETAIN mechanics** | syntax/digest/lineage only                                             |
| generic semantic ledger repair  | **SPLIT/REMOVE**     | domain-specific semantics only                                         |
| closure trust enum              | **RETAIN**           | add reason codes + deterministic consequences                          |
| Obsidian adapter                | **POST-RC7**         | O1 one-way first                                                       |
| host rendering profile          | **RETAIN**           | structured command/tool mapping outside Jinja                          |

---

# 8. Renderer format classification

| Format                | Class                         | Loss / round-trip reality                                       | RC7                        |
| --------------------- | ----------------------------- | --------------------------------------------------------------- | -------------------------- |
| JSON                  | machine serialization         | can be semantically complete                                    | **MUST**                   |
| NDJSON                | ledger/interchange            | may itself be authoritative **only for declared ledger domain** | **MUST**                   |
| Markdown              | human presentation            | semantic projection; never byte round-trip assumption           | **MUST**                   |
| Jinja prompt          | host instruction presentation | lossy wording; no import                                        | **MUST**                   |
| Mermaid               | human graph presentation      | lossy bounded projection                                        | **SHOULD**, reuse existing |
| Graphify              | semantic graph projection     | graph-only subset                                               | **SHOULD**, existing       |
| JSONC                 | human config                  | comments/canonicalization complicate round trip                 | POST                       |
| YAML                  | config/interchange            | typing/alias semantics need constraints                         | POST                       |
| TOML                  | config/interchange            | only suitable bounded schemas                                   | POST                       |
| JSON-LD               | external semantic interchange | mapping-specific, not universal lossless                        | POST                       |
| HTML                  | presentation                  | one-way                                                         | POST                       |
| DOT                   | graph projection              | graph semantics only                                            | POST                       |
| GraphML               | external graph interchange    | graph-only                                                      | POST                       |
| JSON Canvas           | spatial graph presentation    | deliberately lossy                                              | POST                       |
| SVG                   | final visual                  | presentation only                                               | POST                       |
| SARIF                 | machine integration           | finding subset only                                             | POST                       |
| JUnit XML             | machine integration           | test/gate subset only                                           | POST                       |
| CSV/TSV               | lossy tabular export          | explicitly lossy                                                | POST                       |
| Obsidian vault bundle | ecosystem/human projection    | multi-artifact lossy read model                                 | POST                       |

Критическая мысль: **NDJSON не является authority по причине формата**. `eha.ndjson` authority, потому что domain contract назначил его authority. Экспортированный `repair-cases.ndjson` им не становится.

---

# 9. SIB/EHA portability critique

Три SIB meanings достаточно общие, чтобы быть **CodeSleuth maturity methodology**, но не надо делать следующий логический прыжок: будто любой repository объективно уже содержит однозначный SIB ontology.

### Если repository не имеет clear acceptance authority

Correct result:

```text
profile proposal exists
acceptance authority unresolved
EHA claimability = unavailable
```

Не «CodeSleuth нашёл похожие CI jobs и решил, что это канон».

### Если есть две plausible authority models

Planning правильно требует представить обе. Это сохранить.

Human adjudication выбирает **policy**, а не ретроспективно делает одну archaeological interpretation «всегда истинной».

### SIB0 completeness

SIB0 portable только если существует способ честно определить universe.

В brownfield repo возможен результат:

> «Found 14 strongly evidenced capability classes; completeness not established.»

Это полезный вывод. Он просто не является SIB0 PASS.

### Acceptance subject

В planning сейчас встречается идея:

```text
ONE exact candidate/profile/environment subject
```

Я бы её исправил.

Для environment matrix предмет acceptance лучше моделировать так:

```text
acceptance subject =
  exact source SHA
  + exact acceptance-profile digest

supporting evidence =
  required run set
  each bound to exact environment/tool identity
```

Иначе multi-environment profile странно превращается в «one environment subject».

### Profile drift

Здесь план корректен:

```text
same SHA + new profile digest != same acceptance claim
```

Сохранить.

### Tool/runtime drift

Если identity materially included в profile, старый run остаётся historical evidence, а требуемая новая environment/tool configuration должна получить fresh evidence.

### `NOT_APPLICABLE`

Разрешать только obligation-level, с authority-backed rationale.

Не использовать как замену:

* missing test;
* unavailable service;
* unsupported runner;
* inconvenient platform.

### Recursive repair

Автоматический repair должен быть конечным state machine, не «пока модель не устанет».

---

# 10. Repair-loop critique

Сама цепочка хорошая:

```text
A FAIL
 -> RepairCase
 -> RepairPacket
 -> host mutation
 -> re-observation
 -> B
 -> fresh EHA
```

Она совпадает с существующим EHA Repair contract, где campaign не модифицирует свой target, а repair создаёт новый SHA.

Но RC7 следует разделить три разные вещи:

### Diagnosis

Non-authoritative reasoning:

```text
what appears wrong?
which authority disagrees?
what remains uncertain?
```

### Mutation authorization

Deterministic validated policy:

```text
may paths X be changed?
is source evidence fresh?
is architecture still closed?
is closure trustworthy enough?
```

### Host execution

Host-owned actions.

Repair strategy не получает permission только потому, что diagnosis кажется убедительной.

Дополнительно нужен stop state для:

`REPRODUCTION_INCONCLUSIVE`

и желательно:

`HOST_POSTCONDITION_FAILED`

Сейчас их можно выразить существующими generic states, но явные states значительно уменьшают семантическую импровизацию.

---

# 11. Obsidian boundary

Planning research здесь в целом правильный.

Правильная стрелка:

```text
CodeSleuth authority
  -> typed object
  -> Obsidian projection
```

и **никакой обратной стрелки в RC7**.

Почему эта граница действительно нужна, а не просто звучит аккуратно: официальный Obsidian API позволяет plugin'у реально изменять vault files через `Vault.process()` и менять frontmatter через `FileManager.processFrontMatter`. То есть future plugin технически вполне способен превратить YAML property в write-back source, если его не остановить контрактом. ([Developer Documentation][1])

Поэтому:

* edited Properties → **not input authority**;
* backlinks → **not canonical edges**;
* Base formulas → **not engineering conclusions**;
* Canvas edges → **not lineage**;
* plugin refresh → okay;
* plugin adjudication action → только proposal/request в явный CodeSleuth domain API.

O1 pluginless export хорош.

O2 import и O3 plugin bridge не принадлежат RC7.

---

# 12. Recommended minimal RC7 architecture

Вот RC7, который я бы заморозил.

```text
EXISTING AUTHORITIES
├─ Git/source
├─ findings + amendments
├─ EHA ledger
└─ protected capability registry

ONE NEW DOMAIN AUTHORITY
└─ implementation ledger
   └─ accepted-plan execution facts only

PROJECT MATURITY BINDING
project-native authority
   OR explicitly adopted ProjectSibProfile
        ↓
immutable AcceptanceProfileSnapshot
        ↓
existing EHA ledger v2

REPAIR
EhaRepairCase      derived
        ↓
EhaRepairPacket    validated/non-authoritative
        ↓
HostExecutionProfile
        ↓
Jinja presentation
        ↓
host mutation
        ↓
postcondition observer
        ↓
new SHA
        ↓
fresh EHA

LEDGER RECOVERY
shared byte/digest/lineage primitives
        ↓
domain validator/recovery policy
        ↓
domain-owned authority-generation decision

LEARNING
fresh accepted repair
        ↓
RepairLearningRecord
        ↓
preservation proposal
        ↓
explicit promotion
        ↓
existing protected-capability registry

PROJECTION
JSON / NDJSON / Markdown / Jinja
+ existing Mermaid where useful
```

Вот это уже RC7. Всё остальное может жить счастливо в следующих releases, не пытаясь одновременно стать ETL framework, graph interchange platform и personal knowledge management ecosystem.

---

# 13. Exact planning-document changes required before freeze

| Document                                 | Required pre-freeze change                                                                                                  |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `RC7-PLANNING-INDEX.md`                  | добавить canonical authority ownership matrix и зафиксировать один acceptance-profile owner                                 |
| `RC7-FEATURE-PLAN.md`                    | разделить generic structural ledger primitives и domain semantic recovery                                                   |
| `RC7-FEATURE-PLAN.md`                    | запретить Implementation Ledger дублировать EHA verdicts                                                                    |
| `RC7-FEATURE-PLAN.md`                    | убрать generic arbitrary-repo Markdown↔NDJSON framework из RC7                                                              |
| `RC7-SIB-EHA-MATURITY-LOOPS.md`          | определить `ProjectSibProfile` authority modes                                                                              |
| `RC7-SIB-EHA-MATURITY-LOOPS.md`          | заменить ambiguous candidate/profile/environment identity на SHA + immutable profile snapshot + environment evidence matrix |
| `RC7-SIB-EHA-MATURITY-LOOPS.md`          | определить deterministic repair-state transitions и attempt bounds                                                          |
| `RC7-SIB-EHA-MATURITY-LOOPS.md`          | добавить non-reproducible failure handling                                                                                  |
| `RC7-EBCA-GAP-PLAN.md`                   | удалить возможность прочитать human acceptance limitation как substitute for SIB0 completeness                              |
| `RC7-EBCA-GAP-PLAN.md`                   | определить consequence для `DEGRADED` closure                                                                               |
| `RC7-EBCA-GAP-PLAN.md`                   | закрепить ClaimEnvelope как non-persistent view/interface                                                                   |
| `RC7-REPAIR-PACKET-RENDERING.md`         | вынести command/tool semantics из Jinja в structured host profile                                                           |
| `RC7-STRUCTURED-OBJECT-MULTIRENDERER.md` | сократить mandatory RC7 renderers до минимального набора                                                                    |
| `RC7-STRUCTURED-OBJECT-MULTIRENDERER.md` | сделать registry internal/static, не generic plugin framework                                                               |
| `RC7-CONTEXT-EPISTEMICS-DISPOSITION.md`  | явным образом маркировать LearningRecord root-cause fields как derived reasoning                                            |
| `RC7-CONTEXT-EPISTEMICS-DISPOSITION.md`  | preservation candidate продвигается только в existing protected registry                                                    |
| `RC7-OBSIDIAN-ADAPTER-RESEARCH.md`       | зафиксировать O1/O2/O3 как post-RC7 delivery; RC7 максимум research fixture                                                 |
| consolidated RC7 spec                    | определить exact recovery-generation ownership для findings/EHA/implementation отдельно                                     |
| consolidated RC7 spec                    | определить schema migration существующего `eha.ndjson`, не новую authority                                                  |

---

# 14. Things that must NOT be implemented in RC7

1. Generic CRUD over evidence/claims/ledgers.
2. Generic claim persistence database.
3. Generic semantic Ledger Repair capable of rewriting/switching arbitrary domain authorities.
4. Parallel generic EHA ledger.
5. Independent authoritative `AcceptanceProfile` beside `ProjectSibProfile`.
6. Generic arbitrary-project Markdown↔NDJSON mapping framework.
7. Runtime-loadable universal renderer plugin system.
8. Full JSON-LD/GraphML/SARIF/JUnit ecosystem suite.
9. Bidirectional Obsidian synchronization.
10. Obsidian plugin with authority write-back.
11. Generic Negative Claims ledger.
12. `FORBIDDEN_INFERENCE` graph.
13. R0-R3 universal mutation controller.
14. General production safety policy engine.
15. ROAP implementation.
16. Full traceability completeness auditor.
17. Universal assurance-case framework.
18. SLSA/attestation subsystem.
19. Reproducible-build framework.
20. CodeSleuth-owned workflow scheduler/runtime.

---

# 15. Direct contradictions with EBCA thesaurus

## Definite contradiction: SIB0 completeness escape hatch

The combination of:

> uncontrolled/incomplete discovery universe

plus:

> human acceptance of limitation

must **not** produce SIB0 completeness.

EBCA's `Unknown remains unknown` is stronger.

This needs wording correction before freeze.

## Potential contradiction: Markdown semantic import

The thesaurus says:

```text
authority -> derived state -> context -> presentation
```

and direction does not reverse.

Therefore any RC7 Markdown importer that writes authoritative domain state without a distinct import/proposal/adjudication boundary would violate EBCA.

Current planning does not explicitly mandate that violation, but its generic Markdown→domain→NDJSON ambition leaves the door open. Close it before freeze.

## Potential contradiction: independently editable AcceptanceProfile

If both `ProjectSibProfile` and `AcceptanceProfile` can independently encode required gates/environments/obligations, RC7 violates authority ownership even if both are Git-tracked.

One material truth class gets one semantic owner.

## No contradiction found in these areas

The following are aligned strongly with EBCA and should survive consolidation:

* exact-head non-transfer;
* failed-subject immutability;
* non-binary outcomes;
* source rehydration;
* derived Graphify/Mermaid boundary;
* Jinja non-authority;
* Obsidian one-way projection;
* regression witness promotion boundary;
* Context Epistemics deferral;
* postcondition verification.

---

# Final decision

**DO NOT FREEZE RC7.**

The architecture is close, but freeze should happen only after the four BLOCKERs are resolved and the RC7 surface is cut down.

The biggest architectural correction is not adding anything. It is **removing genericity**:

```text
domain authorities stay explicit
shared mechanics stay small
profiles have one owner
repair never becomes a super-authority
renderers remain downstream
learning remains derived
automatic loops terminate deterministically
unknown never becomes PASS by adjudicative optimism
```

With those corrections, the planning set can become a very coherent RC7. Without them, implementation would likely produce exactly the kind of polished, internally consistent duplicate truth system that EBCA exists to prevent.

[1]: https://docs.obsidian.md/Plugins/Vault?utm_source=chatgpt.com "Vault - Developer Documentation"
