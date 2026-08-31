# Context Epistemics for Evidence-Based Code Analysis

## Теория истинных, ложных, неизвестных и запрещённых утверждений в LLM-assisted software engineering

### 1. Назначение

Большие языковые модели способны эффективно рассуждать над кодом, архитектурой, журналами исполнения и инженерной документацией. Однако модель не обладает встроенным механизмом, который гарантированно отличает:

* факт от правдоподобного предположения;
* текущее состояние от устаревшего;
* authoritative source от производного представления;
* отсутствие доказательства от доказательства отсутствия;
* наблюдаемую связь от привычного паттерна;
* допустимый inference от логически привлекательного, но недоказанного перехода.

Для текстовой задачи такая ошибка часто остаётся просто неверным ответом.

Для coding agent она может стать физической мутацией системы:

```text
неверно реконструированное состояние
        ↓
логически последовательное решение
        ↓
корректно выполненная команда
        ↓
неверная мутация реальной системы
```

Именно поэтому безопасность LLM-assisted engineering нельзя сводить к качеству рассуждения модели.

Главная задача состоит в другом:

> **Модель не должна самостоятельно реконструировать истинное состояние мира там, где это состояние может быть предъявлено, проверено и типизировано.**

---

# 2. Основная модель

LLM рассматривается как **inference authority**, но не как authority состояния системы.

```text
LLM =
    inference authority

LLM !=
    state authority
    evidence authority
    ownership authority
    acceptance authority
    execution authority
```

Её задача:

> из предъявленного доказанного состояния построить хороший следующий вывод.

Её задача не состоит в том, чтобы:

> догадаться, какое состояние сейчас, вероятно, истинно.

---

# 3. Слои реальности и рассуждения

Минимальная архитектура состоит из четырёх слоёв.

```text
REAL WORLD
Git / filesystem / DB / host / CI / API
        ↓
AUTHORITATIVE FACTS
exact SHA / refs / schema / manifests / durable ledgers
        ↓
BOUNDED CONTEXT PROJECTION
отобранное представление фактов для конкретной задачи
        ↓
LLM REASONING
claims / hypotheses / plans / decisions
```

Ключевой инвариант:

> **Нижний слой не приобретает authority верхнего слоя только потому, что модель сочла его убедительным.**

Следовательно:

* summary не становится repository truth;
* report не становится acceptance authority;
* Mermaid graph не становится source authority;
* сообщение другого агента не становится host truth;
* branch name не становится commit identity;
* совпадающий tree не становится acceptance identity;
* successful CI не становится EHA verdict.

---

# 4. Главная опасность: ложное состояние, а не галлюцинация

Обычная галлюцинация часто выглядит подозрительно:

```text
"такой API существует"
```

и её можно проверить.

Гораздо опаснее ложное состояние:

```text
"мы на staging"
"эта директория generated"
"этот commit уже принят"
"этот файл принадлежит нашей системе"
"эта migration уже применена"
"этот runner зарегистрирован правильно"
```

После принятия ложной предпосылки дальнейшее рассуждение модели может быть полностью рациональным.

Пример:

```text
FALSE PREMISE:
".opencode/state полностью принадлежит CodeSleuth"

        ↓

REASONABLE IMPLEMENTATION:
recursive delete

        ↓

CORRECT EXECUTION

        ↓

REAL DATA LOSS
```

Ошибка находится не в алгоритме удаления.

Ошибка находится в **эпистемическом статусе ownership claim**.

---

# 5. Почему длинный контекст не решает проблему

Увеличение context window не эквивалентно увеличению достоверности.

Длинный контекст содержит:

* старые и новые состояния одновременно;
* отменённые решения;
* устаревшие SHA;
* старые acceptance results;
* промежуточные гипотезы;
* summaries других summaries;
* конкурирующие explanations;
* повторяющиеся похожие сущности.

Attention не выполняет запрос:

```text
SELECT latest_authoritative_truth
FROM context
WHERE subject = target;
```

Поэтому модель может извлечь наиболее убедительный, а не наиболее authoritative фрагмент.

Следствие:

> **До увеличения объёма контекста необходимо определить, какие части контекста имеют право участвовать в принятии данного решения.**

Контекст должен обладать как минимум:

* provenance;
* authority;
* freshness;
* scope;
* invalidation state;
* relationship to current target identity.

---

# 6. Epistemic states

Для инженерного утверждения недостаточно бинарного `true / false`.

Минимально необходимы следующие состояния.

## CONFIRMED

Утверждение подтверждено authority соответствующего типа.

Пример:

```text
targetSha =
716bacba27515ab57667a1a21e072a95f2c50199
```

подтверждено literal Git ref / checkout.

## CONTRADICTED

Существует authoritative evidence, несовместимое с утверждением.

Пример:

```text
claim:
main points to SHA X

authority:
Git ref points to SHA Y
```

## UNKNOWN

Имеющихся данных недостаточно.

Это не эквивалент `false`.

## CONFLICTED

Существуют два несовместимых свидетельства, и authority ordering пока не разрешил конфликт.

## CLAIMED

Утверждение предъявлено человеком, агентом, отчётом или производным представлением, но ещё не прошло соответствующую проверку.

## CORROBORATED

Есть независимое подтверждение некоторого наблюдаемого следствия, но ещё нет authority, способного доказать сам claim.

Пример:

```text
Cursor:
"runner service запущен"

GitHub:
queued job -> in_progress
```

Это хорошо corroborates утверждение, но не обязательно доказывает всю локальную конфигурацию runner.

---

# 7. Fundamental Unknown Rule

Одна из важнейших ошибок генеративных моделей:

```text
нет доказательства X
        ↓
X, вероятно, false
```

или обратная:

```text
нет доказательства NOT X
        ↓
X, вероятно, true
```

Оба перехода запрещены.

Базовое правило:

> **UNKNOWN не разрешается автоматически ни в TRUE, ни в FALSE.**

Образно:

> Если выключили свет, модель не получает права утверждать, что чёрное стало белым.

Недоступность наблюдения меняет статус знания, а не состояние объекта.

```text
observation unavailable
        ↓
UNKNOWN

not:

observation unavailable
        ↓
opposite value
```

---

# 8. Negative Claims

## 8.1 Определение

Negative Claim является durable knowledge о том, **какой вывод нельзя считать установленным**.

Он нужен не столько для утверждения отрицательного факта, сколько для блокирования опасного inference shortcut.

Положительный claim отвечает:

> что известно?

Negative Claim отвечает:

> какие правдоподобные выводы нельзя повышать до знания?

---

# 9. Классы Negative Claims

## 9.1 Contradicted Claim

```text
X = false
```

Существует evidence, доказывающее несовместимое состояние.

Пример:

```text
"main points to SHA A"
```

при authoritative ref `SHA B`.

---

## 9.2 Unproven Claim

```text
X may be true
but X is not established
```

Этот класс особенно важен для destructive operations.

Пример:

```text
"Вся .opencode/state принадлежит CodeSleuth"
```

не доказано manifest'ом ownership.

Для чтения это может быть допустимой гипотезой.

Для рекурсивного удаления этого недостаточно.

---

## 9.3 Forbidden Inference

Форма:

```text
A does NOT imply B
```

Здесь утверждается не `B = false`.

Утверждается:

> переход от A к B не имеет достаточного основания.

Примеры:

```text
parent EHA PASS
    -/-> child EHA PASS
```

```text
same tree
    -/-> same acceptance identity
```

```text
path under .opencode
    -/-> CodeSleuth ownership
```

```text
GitHub workflow SUCCESS
    -/-> SIB/EHA PASS
```

```text
service process exists
    -/-> correct service registration
```

```text
tests found no failure
    -/-> feature correctness
```

```text
branch is called release
    -/-> accepted release candidate
```

Forbidden Inference можно понимать как **negative edge** графа рассуждений:

```text
A -/-> B
```

Это не отсутствие известного ребра.

Это durable knowledge:

> данный переход был рассмотрен и признан необоснованным.

---

# 10. Структура durable Negative Claim

Рекомендуемая форма:

```text
id:
subject:
claim:

status:
  CONTRADICTED | UNPROVEN | FORBIDDEN_INFERENCE

authority:
evidence_refs:

reason:

danger:
  какое неверное действие может следовать из claim

consequence:
  какие решения запрещены при текущем статусе

scope:
  где claim применим

recorded_at:
source_identity:

reopen_condition:
  какое новое evidence разрешает снова рассмотреть claim
```

Особенно важен `reopen_condition`.

Без него следующая модель может снова выполнить ту же ошибочную реконструкцию и считать её новой гипотезой.

---

# 11. Negative Claims как антидот к pattern completion

Code generator оптимизирован на завершение структур.

Условно:

```text
вижу 80% знакомого pattern
        ↓
достраиваю оставшиеся 20%
```

Для генерации локальной функции это полезная способность.

Для восстановления реального состояния инфраструктуры это опасно.

Negative Claim помещает рядом с привлекательным pattern знание:

```text
выглядит как X
    !=
доказано как X
```

Таким образом он специально противодействует statistical pattern completion там, где требуются authoritative facts.

---

# 12. Retrieval должен возвращать не только факты, но и запреты

Обычный RAG обычно ищет положительно релевантный контекст.

Для evidence-based engineering этого недостаточно.

При работе над конкретным объектом retrieval должен возвращать:

```text
positive facts
+
relevant contradictions
+
relevant unproven assumptions
+
forbidden inference edges
+
previous failure modes
```

Например, изменение `install.py` должно приносить в context не только installer contract, но и:

```text
NEGATIVE CLAIM

Do not infer ownership from location under `.opencode`.

Rejected inference:
`.opencode/**` is CodeSleuth-owned.

Authority:
managedFiles + explicit runtime namespaces.

Failure mode:
destructive removal of host-owned material.
```

---

# 13. Context as an Epistemic Type System

Контекст модели следует рассматривать не как набор строк, а как типизированные утверждения.

Например:

```text
Claim<GitAuthority>
Claim<FilesystemObservation>
Claim<DurableEvidenceAuthority>
Claim<DerivedReport>
Claim<ModelInference>
Claim<ExternalOperatorReport>
```

Нельзя использовать:

```text
Claim<DerivedReport>
```

там, где операция требует:

```text
Claim<DurableEvidenceAuthority>
```

Так же как компилятор не должен молча преобразовывать произвольную строку в trusted pointer.

Эта модель превращает многие ошибки LLM в разновидность **epistemic type error**.

---

# 14. Action gates

Особенно строгая дисциплина нужна между:

```text
OBSERVE
CLAIM
DECIDE
MUTATE
```

Разрешённая схема:

```text
OBSERVE
    ↓ provenance
CLAIM
    ↓ evidence binding
DECIDE
    ↓ authority + risk gate
MUTATE
    ↓ postcondition verification
NEW OBSERVED STATE
```

Опасный shortcut:

```text
CLAIM → MUTATE
```

Для destructive или irreversible mutation требуется более высокий evidence threshold, чем для чтения или формирования гипотезы.

Пример:

```text
READ:
UNPROVEN может быть допустимой hypothesis

DELETE:
UNPROVEN = STOP
```

---

# 15. Risk-weighted epistemics

Требуемая сила доказательства должна зависеть от цены ошибки.

```text
low-risk observation
    → weaker evidence acceptable

reversible edit
    → stronger identity/ownership evidence

deployment
    → exact target + environment evidence

destructive DB/filesystem operation
    → authoritative environment
      + ownership
      + target
      + backup/recovery state
      + explicit mutation scope
```

Следовательно:

> модель не обязана одинаково доказывать каждый вывод, но обязана увеличивать epistemic threshold вместе с blast radius.

---

# 16. Relationship to SIB/EHA

SIB/EHA являются частным случаем общей context epistemics.

## SIB

Отвечает:

> какой baseline уже доказан?

## EHA

Запрещает inference:

```text
accepted identity A
    -/->
different identity B accepted
```

## Protected capability registry

Запрещает молчаливо переопределять архитектурные границы.

## Durable evidence store

Не позволяет conversation memory стать acceptance authority.

## Context projection

Ограничивает рабочее пространство модели релевантным текущему решению знанием.

## Negative Claims

Сохраняют не только подтверждённые пути, но и уже отвергнутые inference paths.

---

# 17. Конечная цель системы

Цель не состоит в том, чтобы:

* сделать LLM всезнающей;
* дать ей бесконечный context;
* заставить её никогда не ошибаться.

Цель:

> **Сделать ошибочную реконструкцию состояния мира дороже и труднее, чем правильную.**

Правильные inference paths должны быть:

* короткими;
* authoritative;
* свежими;
* явно представленными.

Опровергнутые paths должны быть:

* сохранены;
* легко извлекаться;
* явно запрещены.

Неизвестные paths должны:

* оставаться UNKNOWN;
* требовать дополнительного evidence перед опасным действием.

---

# 18. Главный инженерный принцип

```text
LLM may infer.

LLM may not silently promote
plausibility into state authority.
```

Или в более человеческой форме:

> **Модель имеет право думать, что что-то вероятно.
> Она не имеет права действовать так, будто это уже доказано, если цена ошибки материальна.**

---

# 19. Центральная формула

```text
authoritative state
+ explicit claim status
+ relevant negative knowledge
+ bounded context
+ risk-dependent action gate
=
grounded LLM engineering
```

Главная роль Negative Claims:

> **не уменьшить способность модели рассуждать, а ограничить её право использовать статистическую правдоподобность вместо знания там, где ошибка способна изменить или уничтожить реальную систему.**
