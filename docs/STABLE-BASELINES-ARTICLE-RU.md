# Stable Baselines: как перестать путать «мы написали систему» с «она работает»

## Предисловие: самый опасный момент после большого рефактора

У большого рефактора есть странная финальная стадия. Код уже переписан. Старые модули торжественно удалены. Новая архитектура выглядит чище, зависимости направлены в правильную сторону, диаграмма помещается на один экран, а люди снова начали использовать выражение «теперь всё просто» без нервного смеха.

И именно в этот момент проект особенно легко испортить.

Потому что в issue tracker уже лежат задачи следующего релиза. Один разработчик хочет вернуть старую функцию, второй уже добавляет новую, третий чинит migration path, четвёртый обнаружил, что Windows ведёт себя иначе, а кто-то тихо поставил `xfail` на тест, который «пока мешает двигаться дальше». Через две недели в одной ветке живут последствия рефактора, восстановление старых возможностей, новые features, интеграционные дефекты и релизный polish.

После этого на простой вопрос «что именно сейчас сломано?» начинается философский семинар.

Мы достаточно раз наблюдали подобный момент в реальных кодовых проектах, чтобы перестать искать ещё один workflow для Jira и начать искать более полезную вещь: **точки, в которых можно доказанно менять тип работы**.

Так появилась модель Stable Baselines.

Она не претендует на статус нового международного стандарта и не требует сертифицированного консультанта с цветными стикерами. Термины `SIB0`, `SIB1` и `SIB2` мы вводим как рабочую инженерную нотацию для состояний, которые существуют и без названий, но без названий удивительно легко смешиваются.

Коротко идея выглядит так:

```text
SIB0 = мы стабилизировали архитектурную форму
SIB1 = мы реализовали эту форму
SIB2 = мы доказали, что реализация работает как система
```

А главное практическое правило звучит ещё короче:

> **SIB1 не является безопасной базой для активного feature population. SIB2 является.**

До SIB2 мы в первую очередь строим и доказываем архитектуру. После SIB2 мы начинаем активно наполнять доказанную архитектуру продуктом.

*Все совпадения с известными кейсами из Сети ниже, разумеется, случайны. Сами кейсы, однако, совершенно реальные, ссылки приложены. Мы не утверждаем, что наличие документа с буквами SIB магически спасло бы каждый из этих проектов. Человечество умеет ломать production слишком изобретательно для одной аббревиатуры. Но уроки о разнице между «компонент существует», «компонент протестирован» и «система доказанно работает в композиции» у этих историй очень конкретны.*

---

# 1. Что вообще означает Stable Baseline

Слово *stable* в разработке используется почти как слово «готово»: с большой уверенностью и очень разными значениями.

`stable branch` может означать:

- старый production release;
- ветку, которую давно никто не трогал;
- текущий `main` с зелёным CI;
- ветку, где наконец перестали падать тесты;
- место, куда всем страшно коммитить, и поэтому оно действительно довольно стабильно.

Для Stable Baseline этого недостаточно.

Baseline должен отвечать не на вопрос «кажется ли нам код стабильным», а на вопрос:

> **Какое конкретное утверждение о зрелости этой архитектуры уже доказано для точного состояния репозитория?**

Отсюда три уровня.

| Baseline | Полное имя | Что он доказывает |
| --- | --- | --- |
| **SIB0** | Stable Initialization Baseline | Фундаментальный список capability classes определён и заморожен для текущего архитектурного поколения |
| **SIB1** | Stable Implementation Baseline | Каждый capability class из SIB0 имеет настоящую базовую реализацию и выполняет свой контракт |
| **SIB2** | Stable Integration Baseline | Эти реализации доказанно работают вместе как единая система, а точная композиция прошла canonical acceptance |

Это не три маркетинговых уровня «бронза, серебро, золото». Каждый baseline разрешает сделать более сильное инженерное утверждение, чем предыдущий.

Именно **SIB2** является нормальной базой для строительства нового релиза.

---

# 2. Capability class: почему feature и архитектура не одно и то же

Центральный термин модели - **capability class**.

Capability class - это фундаментальный тип способности, которой архитектура должна обладать. Он шире отдельной функции, команды, endpoint, профиля или UI-действия.

Например:

- CLI - capability class;
- конкретная команда `verify` - feature внутри CLI;
- extension system - capability class;
- Python, Rust и TypeScript profiles - конкретное наполнение этого класса;
- persistent state - capability class;
- дополнительное поле в state-файле обычно не новый capability class;
- context graph - capability class;
- новые relation types, filters и projections обычно его feature population;
- report generation - capability class;
- Markdown, HTML и JSON reports - варианты внутри класса.

Удобный тест такой:

> **Если изменение можно описать как «ещё один экземпляр, вариант, workflow или более глубокая реализация уже существующего типа возможности», это, скорее всего, feature population.**

Например:

```text
Capability class: profile system

SIB2:
  один реально работающий profile

Feature population:
  Python profile
  Rust profile
  TypeScript profile
  security-review profile
  database-analysis profile
```

Или:

```text
Capability class: report generation

SIB2:
  один настоящий Markdown report

Feature population:
  HTML report
  executive brief
  analyst note
  machine-readable JSON report
```

Но если новая feature требует:

- второго execution runtime;
- принципиально новой persistence architecture;
- нового фундаментального orchestration layer;
- новой модели ownership между подсистемами;
- нового типа lifecycle, которого архитектура раньше вообще не знала,

то это уже не просто feature population.

Вы изменили архитектурную форму.

И это не преступление. Просто это надо честно назвать архитектурным изменением, а не прятать его в PR `feat: add convenient option` размером в 14 000 строк.

---

# 3. Feature population: наполнение архитектуры, а не её расширение

**Feature population** - это увеличение продуктовой плотности внутри уже существующих capability classes.

После SIB2 архитектура может быть очень «худой»:

- CLI имеет две команды;
- extension system знает один profile;
- graph умеет один тип projection;
- report subsystem создаёт один формат;
- UI поддерживает один основной flow.

Это уже может быть настоящая, production-grade архитектура, если все заявленные classes существуют, замкнуты end-to-end и проходят acceptance.

Feature population делает её богатым продуктом:

```text
ещё команды
ещё profiles
ещё tools
ещё adapters
ещё workflows
ещё graph relations
ещё report types
лучше UX
глубже domain logic
больше supported environments
```

То есть feature population увеличивает **глубину и плотность**, но не должно молча увеличивать **архитектурную ширину**.

Эта граница особенно полезна во время подготовки релиза. Если запланированная «обычная feature» внезапно требует новый fundamental capability class, release plan больше не описывает обычное наполнение системы. Архитектура снова открылась.

---

# 4. SIB0: Stable Initialization Baseline

SIB0 - точка, в которой мы закончили выяснять, **из каких фундаментальных видов частей состоит система**.

На SIB0:

1. Все известные fundamental capability classes текущего архитектурного поколения перечислены.
2. Для каждого существует явный architectural slot: interface, module boundary, contract, placeholder, skeleton или эквивалент.
3. Основные ownership boundaries понятны.
4. Команда считает capability-class inventory достаточным для реализации текущего замысла.
5. Этот список замораживается для обычной implementation work.

При этом реализации могут быть почти пустыми.

Например:

```text
CLI                 skeleton + help
TUI                 один экран
persistent state    минимальный store/load
extensions          один тестовый loader
reports             один stub-like real path
updates             минимальный happy path
```

SIB0 не заявляет: «архитектура окончательна навсегда».

Он заявляет значительно более умеренную вещь:

> **В рамках текущего архитектурного поколения ordinary planned work больше не должно требовать появления новых фундаментальных capability classes.**

Если после SIB0 выяснилось, что всё-таки нужен новый fundamental class, baseline не «чуть-чуть обновился».

Архитектура снова открыта.

Нужно провести architectural convergence и назначить новый SIB0.

Baseline, чей defining inventory можно тихо менять по четвергам, называется не baseline, а README.

---

# 5. SIB1: Stable Implementation Baseline

После SIB0 начинается implementation recovery или, для нового проекта, просто implementation.

Теперь задача состоит не в том, чтобы придумать ещё архитектуру, а в том, чтобы каждый объявленный capability class стал настоящим.

К SIB1:

- CLI действительно выполняет базовую операцию;
- state действительно сохраняется и восстанавливается;
- extension действительно обнаруживается и загружается;
- report subsystem действительно создаёт output;
- lifecycle действительно проходит базовый цикл;
- graph subsystem действительно строит и запрашивает граф;
- interfaces существуют не только на диаграмме, но и в работающем коде.

SIB1 позволяет сделать утверждение:

> **Мы реализовали архитектуру, которую зафиксировали на SIB0.**

Но SIB1 ещё не позволяет сказать:

> **Эта архитектура доказанно работает как единая система.**

Это принципиальная граница.

Компоненты могут быть прекрасно протестированы по отдельности и очень творчески уничтожать друг друга при композиции.

State работает. UI работает. Controller работает. Extension loader работает.

А теперь extension запускается через controller из TUI, меняет state, update lifecycle в этот момент перечитывает metadata, Windows даёт другой path semantic, и внезапно оказывается, что слово «работает» у каждого компонента было локальным диалектом.

Поэтому:

> **SIB1 не является безопасной базой для активного feature population.**

Между SIB1 и SIB2 основной задачей становится не расширение продукта, а доказательство уже существующей композиции.

---

# 6. SIB2: Stable Integration Baseline

SIB2 появляется, когда все минимальные реализации capability classes не просто существуют, а **доказанно работают вместе**.

Здесь нужны:

- cross-capability integration;
- реальные end-to-end paths;
- persistence/runtime/controller interactions;
- lifecycle behavior;
- migration paths, если они входят в контракт;
- supported environment matrix;
- failure paths;
- canonical full-system acceptance;
- exact repository state, к которому относится evidence.

Формула evidence выглядит скучно, а значит полезно:

```text
exact commit SHA
+
canonical acceptance gate
+
successful result
```

Фраза «эта feature была зелёной неделю назад» не подходит.

Фраза «все PR по отдельности прошли CI» тоже не подходит.

Нужно доказать exact **composed integration state**.

SIB2 позволяет сказать:

> **Реализованная архитектура доказанно работает как система.**

И именно SIB2 является первой нормальной базой для активного feature population и строительства следующего релиза.

SIB2 не является RC. Он может быть архитектурно полным и при этом продуктово очень худым.

Это различие можно выразить так:

> **architecture-complete != release-complete**

---

# 7. MVP и SIB измеряют разные вещи

На первый взгляд SIB2 похож на MVP: система работает, функций мало.

Но они минимальны по разным осям.

**MVP** минимален по продуктовой ценности.

Он спрашивает:

> Какой самый маленький продукт уже позволяет проверить, нужен ли он кому-нибудь?

Поэтому MVP может быть архитектурно страшным:

- один happy path;
- temporary storage;
- shell script;
- hardcoded configuration;
- кусок Python, который после успеха гипотезы предполагается торжественно сжечь.

Это нормально.

Его задача - доказать usefulness.

**SIB** минимален по feature depth внутри уже сформированной архитектуры.

Он спрашивает:

> Представлены ли все фундаментальные виды возможностей и доказана ли архитектурная композиция?

Поэтому можно иметь такую матрицу:

| | Низкая product completeness | Высокая product completeness |
| --- | --- | --- |
| **Низкая architecture completeness** | prototype / MVP | исторически разросшийся монолит, в который страшно смотреть |
| **Высокая architecture completeness** | **SIB2** | release |

SIB2 занимает очень конкретную клетку:

> **архитектура уже настоящая, продукт ещё худой.**

Это и делает его хорошим release construction base.

---

# 8. Канон пострефакторного восстановления

Для крупного refactor полезно разделить два разных процесса:

1. **восстановление архитектуры**;
2. **строительство следующего релиза**.

Сначала:

```text
refactor
→ architectural convergence
→ SIB0
→ implementation recovery
→ SIB1
→ integration recovery
→ acceptance
→ SIB2
```

Потом:

```text
SIB2
→ integration build
→ feature population
→ acceptance
→ RC
→ release
```

## Refactor

Архитектура сознательно перестраивается.

Меняются module boundaries, ownership, persistence, execution paths, dependency direction, state organization или другие фундаментальные элементы.

Код после refactor может стать значительно красивее и при этом временно потерять часть прежних возможностей.

`refactor complete` поэтому означает не:

```text
project stable
```

а скорее:

```text
new architectural form exists
```

## Architectural convergence

Команда перестаёт постоянно менять fundamental topology и определяет полный capability-class inventory текущего архитектурного поколения.

Пока каждый второй день появляется новый фундаментальный тип subsystem, convergence ещё не наступил.

## SIB0

Capability-class inventory заморожен.

Мы уже знаем, **что должно существовать**, даже если часть реализаций ещё skeletal.

## Implementation recovery

Каждый class доводится от placeholder к настоящему базовому implementation path.

Не возвращаются все будущие features. Возвращаются **все архитектурные типы способностей**.

## SIB1

Все capability classes имеют реальные basic implementations и выполняют свои component-level contracts.

Implementation completeness доказана.

Но feature population всё ещё преждевременен.

## Integration recovery

Основной вопрос меняется с:

> «каждая часть написана?»

на:

> «эти части действительно работают вместе?»

Здесь ищутся проблемы в:

- lifecycle;
- state interactions;
- controller/runtime boundaries;
- migrations;
- environment differences;
- failure handling;
- end-to-end paths.

Интеграция при этом, конечно, должна происходить и раньше. `Integration recovery` означает не «мы впервые решили объединить код после полугода раздельной разработки», а **смену основного объекта доказательства**.

## Acceptance

Проверяется exact composed state.

Не память команды о старом зелёном PR.

Не optimistic arithmetic:

```text
A green
B green
C green
therefore A+B+C green
```

Компьютеры почему-то отказываются уважать такую математику.

## SIB2

Новая архитектурная генерация доказанно работает как система.

Теперь можно перестать чинить фундамент и начать активно строить этажи.

*История, про которую невозможно молчать №1: Ariane 5 Flight 501, 1996 год. Ракета разрушилась примерно через 40 секунд после старта. Комиссия ESA установила, что software inertial reference system содержало conversion 64-bit floating-point value в 16-bit signed integer; значение, допустимое для траектории Ariane 5, вышло за диапазон. Особенно выразительно то, что этот software был унаследован от Ariane 4 и функция, приведшая к exception, вообще не требовалась после lift-off. Компонент был зрелым. Код имел историю. Система изменилась. Старое доказательство корректности не доказало новую композицию.[^ariane]*

---

# 9. После SIB2 начинается release construction

SIB2 не надо превращать в вечную dev-ветку.

Он является **доказанной стартовой точкой**.

Release construction выглядит так:

```text
SIB2
→ integration build 1
→ acceptance
→ accepted integration state 1
→ integration build 2
→ acceptance
→ accepted integration state 2
→ ...
→ planned feature population complete
→ RC
→ release
```

Каждый существенный слой должен доказываться на своей exact composition.

Это даёт важный invariant:

> **Green result на старой feature branch не является compatibility evidence для текущего release composition.**

Если stale branch был зелёным два месяца назад, его лучше semantic-transplant/rebase на текущий accepted descendant SIB2 и доказать получившийся head.

Wholesale merge старых файлов - прекрасный способ вернуть уже исправленные баги вместе с feature, как бесплатный подарок покупателю.

*История, про которую невозможно молчать №2: Knight Capital, 1 августа 2012 года. При deployment нового software один из восьми серверов не получил новую версию. На семи серверах новый flag активировал новый code path, а на восьмом - старый dormant code под названием Power Peg. За примерно 45 минут система отправила миллионы ошибочных orders; SEC указывает loss свыше $460 млн. Локально существовали и новый код, и deployment procedure, и серверы, которые «в целом одинаковые». Exact composed production state оказался другим.[^knight]*

---

# 10. Stable Baselines в новой разработке

SIB-модель полезна не только после refactor.

Для greenfield-проекта она даже чище:

```text
product intent
→ architectural exploration
→ capability-class discovery
→ SIB0
→ implementation
→ SIB1
→ integration hardening
→ acceptance
→ SIB2
→ feature population
→ RC
→ release
```

## До SIB0 архитектура имеет право меняться

На этой стадии нормально:

- писать spikes;
- выбрасывать prototypes;
- объединять предполагаемые capability classes;
- разделять один class на два;
- менять ownership boundaries;
- пробовать разные persistence models;
- обнаруживать, что «plugins» на самом деле означают отдельно discovery и execution.

Это exploration.

SIB0 не нужен слишком рано.

Иначе мы просто дадим красивое имя premature commitment.

## SIB0: мы наконец решили, что строим

Предположим, новый developer tool должен иметь:

```text
CLI
TUI
project state
configuration
extension loading
tool execution
update lifecycle
report generation
acceptance infrastructure
```

На SIB0 всё это уже представлено архитектурно.

Но реализации могут быть минимальными.

После SIB0 ordinary implementation больше не должна изобретать новые fundamental categories каждые три PR.

## SIB1: сначала ширина, потом глубина

Greenfield-проекты обладают прекрасной способностью за полгода создать 47 CLI-команд и оставить persistence как `TODO`.

SIB1 заставляет сделать наоборот.

Лучше:

```text
CLI          1 рабочая команда
TUI          1 рабочий flow
plugins      1 рабочий plugin
reports      1 рабочий report
updates      1 рабочий update path
state        1 рабочий persistence path
```

чем:

```text
CLI          47 команд
TUI          placeholder
plugins      TODO
reports      TODO
updates      TODO
state        sqlite.py TODO
```

Первое состояние архитектурно близко к SIB1.

Второе продуктово выглядит бодрее, но всё ещё напоминает very convincing prototype.

## Между SIB1 и SIB2 надо доказать композицию

Пусть:

- TUI умеет обращаться к controller;
- controller умеет запускать tool;
- state умеет сохраняться;
- extension умеет загружаться.

Теперь вопрос:

> Что произойдёт, когда extension запускает tool, tool меняет state, а UI одновременно перечитывает состояние?

Это уже вопрос SIB2.

Именно поэтому SIB1 нельзя превращать в площадку массового feature population.

## SIB2: первая доказанная платформа роста

Новый аналитический продукт на SIB2 может уметь всего:

```text
импортировать один тип данных
нормализовать его
сохранить state
запустить один tool
построить один graph
создать один report
показать результат через один UI flow
```

Для будущего product scope это выглядит бедно.

Но если путь настоящий и full acceptance доказал композицию, это гораздо более сильное состояние, чем система с сорока partly integrated features.

После него можно безопасно наращивать:

```text
10 import formats
20 tools
15 graph relations
5 report templates
несколько UI workflows
новые profiles
```

*История, про которую невозможно молчать №3: Mars Climate Orbiter, 1999 год. NASA указывает причиной потери аппарата failure to translate English units to metric в ground software: одна часть системы предоставляла данные в pound-force seconds, другая ожидала newton-seconds. Обе стороны могли быть вполне реализованы. Интерфейс существовал. Значения даже выглядели как числа, что всегда успокаивает компьютер до последней секунды. Но semantics composition не были доказаны достаточно хорошо.[^mco]*

---

# 11. Stable Baseline как момент смены типа работы

Это, пожалуй, наиболее полезная интерпретация всей модели.

SIB - не просто snapshot.

Это **promotion state**, после которого меняется главный разрешённый тип работы.

### До SIB0

Основная работа:

> исследовать архитектуру.

Можно менять capability-class inventory.

### После SIB0

Основная работа:

> реализовать зафиксированную архитектуру.

Новые fundamental classes требуют явного reopen архитектуры.

### После SIB1

Основная работа:

> доказать композицию.

Не надо компенсировать недоказанную integration quality количеством новых features.

### После SIB2

Основная работа:

> feature population и release construction.

Архитектура теперь является доказанным основанием, а не продолжающимся ремонтом.

При этом SIB levels **не являются календарными phase gates**.

Integration tests можно писать до SIB1.

CI должен работать на всём пути.

Architectural feedback может вернуть нас назад.

Refactoring тоже не запрещён.

Порядок SIB означает не:

> «в понедельник архитектура, во вторник implementation, integration разрешена только в среду».

Он означает:

> **каждый следующий baseline разрешает сделать более сильное утверждение о зрелости конкретного state.**

*История, про которую невозможно молчать №4: GitLab.com, январь 2017 года. После ошибочного удаления данных компания обнаружила, что несколько предполагаемых механизмов backup/replication либо не работали как ожидалось, либо не обеспечивали нужное восстановление; в postmortem GitLab подробно описала последовательность отказов и проблемы recovery. Это очень хороший антипример фразы «у нас есть backup» как законченного утверждения. Capability существует только тогда, когда доказан его необходимый end-to-end contract, а recovery особенно любит проверять эту философию в 3 часа ночи.[^gitlab]*

---

# 12. Что скажут классические школы разработки

Новая терминология особенно полезна, если переживает нападение людей, у которых уже есть своя терминология.

## Agile / Scrum: «Вы заново изобрели waterfall»

Критика очевидна:

```text
SIB0 → SIB1 → SIB2
```

выглядит как architecture phase → implementation phase → integration phase.

Если применять это именно так, критик прав.

Но SIB levels - **states of evidence**, не calendar stages.

Интеграция может идти постоянно. Tests могут появляться с первого дня. Новый feedback может инвалидировать SIB0.

Стрелки определяют порядок силы assertions:

```text
SIB0: shape known
SIB1: shape implemented
SIB2: implementation proven integrated
```

А не очередь доступа разработчиков к клавиатуре.

SIB0 также не замораживает requirements.

Он замораживает только fundamental capability-class inventory текущего architectural generation.

Можно менять workflows, добавлять features и улучшать продукт.

Если же изменение требует новый fundamental class, оно должно перестать маскироваться под ordinary feature.

## XP / Continuous Integration: «Интегрировать надо всё время»

Абсолютно.

Continuous Integration - practice на всём пути.[^ci]

`integration recovery` после SIB1 не означает, что до этого все полгода сидели в отдельных ветках и впервые решили познакомить свои модули.

Это означает, что после достижения implementation completeness основным unresolved question становится integration completeness.

Хорошая CI discipline может сделать SIB1 и SIB2 почти соседними состояниями или даже позволить одному exact commit удовлетворить обоим наборам критериев.

Никакой методологический нотариус не требует держать commit трое суток между SIB1 и SIB2.

## Continuous Delivery / DORA: «Software должно постоянно быть releasable»

Для зрелой системы в обычном feature-development режиме - желательно.

Именно поэтому нормальная жизнь продукта происходит после SIB2.

SIB0/SIB1 особенно нужны:

- при создании новой architecture generation;
- во время крупного refactor;
- после сознательного нарушения прежней architecture shape.

Модель не говорит:

> перестаньте быть continuously releasable.

Она говорит:

> если архитектурная операция временно уничтожила доказанный integrated state, не маскируйте это feature velocity; сначала восстановите новый SIB2.

Небольшая architecture evolution может пройти:

```text
SIB2a
→ controlled change
→ SIB0'
→ SIB1'
→ SIB2b
```

в одном хорошем PR.

SIB не требует медленности.

Он требует точности утверждений.

## Lean / Kanban: «SIB0 замораживает knowledge слишком рано»

Именно поэтому перед ним architectural convergence.

До SIB0 можно держать alternatives, делать spikes, разделять и объединять concepts, выбрасывать prototypes.

SIB0 означает:

> **мы накопили достаточно knowledge, чтобы перестать считать fundamental topology обычным открытым вопросом текущей реализации.**

Если новое знание это опровергло, baseline инвалидируется явно:

```text
SIB0
→ новое архитектурное знание
→ reopen architecture
→ convergence
→ SIB0'
```

Это не запрет на learning. Это бухгалтерия architectural change, только полезная.

## Evolutionary Architecture / SAFe: «Архитектура должна жить»

Согласны.

Ключевое выражение здесь: **architectural generation**.

SIB0 не заявляет вечную завершённость архитектуры. Он фиксирует её для текущего поколения ordinary planned work.

SIB2 можно даже рассматривать как более forensic-родственника Architectural Runway: runway говорит, что технической основы достаточно для ближайших features; SIB2 дополнительно указывает exact proven state, от которого мы готовы эти features строить.[^runway]

Runway живёт непрерывно. SIB даёт проверяемые точки доказательства.

Можно иметь:

```text
living architecture
      ↓
SIB2a → evolution → SIB2b → evolution → SIB2c
```

Редкий случай, когда с SAFe можно согласиться и успеть уйти до того, как кто-то откроет PI Planning spreadsheet.

## Product purist: «А пользователь вообще просил вашу прекрасную архитектуру?»

Очень хороший вопрос.

Если SIB заменяет product discovery, мы занимаемся architecture cosplay.

Поэтому MVP и SIB разделены.

```text
MVP:
  стоит ли строить продукт?

SIB:
  способна ли выбранная архитектура безопасно нести его развитие?
```

Для неизвестного рынка совершенно разумно:

```text
idea
→ crude prototype
→ MVP
→ hypothesis validated
→ serious architecture
→ SIB0
→ SIB1
→ SIB2
```

Сначала можно написать страшный Python script и проверить, нужен ли он кому-нибудь. Не надо проектировать cathedral для продукта, который пока попросил только один знакомый в Telegram.

## PMI / configuration management: «Где scope baseline и change-control board?»

Нигде, если они проекту не нужны.

SIB - engineering baseline, а не полный project-management baseline.

Он отвечает:

- что представляет архитектурную форму;
- реализована ли она;
- доказана ли композиция;
- какой exact state это подтверждает.

Он не описывает budget, staffing, procurement и contractual scope.

В регулируемом проекте SIB2 SHA + acceptance evidence может спокойно стать configuration item внутри formal change control.

Exact SHA, к слову, несколько труднее интерпретировать творчески на steering committee, чем фразу «solution baseline substantially achieved».

## SRE: «Ваши tests зелёные. Production ещё не голосовал»

Тоже верно.

SIB2 означает Stable **Integration** Baseline, а не доказанную вечную production reliability.

Для service architecture canonical acceptance должен включать нужный объём production-like evidence: packaged artifacts, migrations, load, rollback, staging и так далее.

Но реальные traffic patterns всё равно способны сообщить неприятную новость.

Поэтому вполне естественна цепочка:

```text
SIB2
→ feature population
→ acceptance
→ RC
→ canary / staged rollout
→ release
```

*История, про которую невозможно молчать №5: CrowdStrike, июль 2024 года. Компания выпустила Rapid Response Content update для Windows sensor; из-за bug в Content Validator проблемный instance прошёл validation, а при загрузке привёл к out-of-bounds read и системным crash/BSOD на затронутых Windows hosts. В собственном PIR CrowdStrike после инцидента перечислила меры, среди которых дополнительное testing, content interface testing и staged rollout, начинающийся с canary. Особенно полезный урок для нашей темы: feature population внутри давно существующего delivery mechanism всё равно способно открыть новый failure mode. «Это всего лишь content/config update» не является exemption от acceptance.[^crowdstrike]*

---

# 13. Самая серьёзная критика SIB

Самая сильная атака всё-таки приходит от Continuous Integration и Evolutionary Architecture:

> **Диаграмма SIB слишком легко читается как последовательность фаз.**

Это действительно опасно.

Поэтому каноническое уточнение должно звучать так:

> **SIB0, SIB1 and SIB2 are promotion states, not isolated development phases. Their ordering defines the increasing strength of claims that may be made about a repository state. Engineering activities such as integration, testing, architectural feedback and refactoring may occur continuously across the progression.**

По-русски:

> **SIB0, SIB1 и SIB2 - состояния доказанной зрелости, а не календарные фазы. Их порядок определяет силу утверждения, которое разрешено сделать о системе, а не момент, когда разрешено впервые писать тесты, интегрировать код или получать архитектурный feedback.**

Это важнее, чем кажется.

Мы можем интегрировать с первого commit.

Просто до SIB2 мы не имеем права говорить, что integrated composition **доказана**.

---

# 14. Практический канон в одной таблице

| Состояние | Что уже доказано | Что является основной работой | Что пока нельзя считать нормальным режимом |
| --- | --- | --- | --- |
| До SIB0 | Архитектура ещё исследуется | discovery, spikes, boundaries, capability-class inventory | притворяться, что fundamental topology уже frozen |
| **SIB0** | Архитектурная форма зафиксирована | реализация каждого capability class | тихо добавлять новые fundamental classes |
| **SIB1** | Все classes базово реализованы | integration hardening, end-to-end evidence | активный feature population |
| **SIB2** | Композиция доказанно работает | release construction и feature population | считать любой новый architecture primitive «просто feature» |
| Accepted integration build | Точный descendant SIB2 снова прошёл gate | следующий слой feature population | опираться на старые green results вместо текущего SHA |
| **RC** | Запланированная product composition доказана | final release validation / rollout | продолжать бесконтрольно менять scope |
| **Release** | Версия опубликована и принята процессом release | operation, feedback, next cycle | считать release автоматически вечным SIB2 без нового решения |

---

# 15. Простые правила, которые из этого следуют

1. **Baseline всегда должен указывать на exact state.** Лучше SHA, а не «примерно вот эта ветка».
2. **SIB0 замораживает capability-class inventory, а не все requirements.**
3. **Новый fundamental capability class после SIB0 открывает новую architectural lineage.**
4. **SIB1 доказывает implementation completeness, но не даёт права массово наращивать features.**
5. **SIB2 требует full-system acceptance exact composition.**
6. **Feature population начинается нормально только от SIB2 или доказанного descendant.**
7. **Зелёный старый PR не является evidence для новой композиции.**
8. **Acceptance нельзя ослаблять, чтобы change «влез» в baseline.** Тогда вы не доказали baseline, вы переписали определение слова «зелёный».
9. **Stale feature branches лучше semantic-transplant/rebase onto current accepted state, а не wholesale merge старых файлов.**
10. **Promotion baseline - отдельное решение.** Feature work не должно случайно двигать baseline ref.

---

# 16. А в чём тогда настоящая ересь Stable Baselines

Agile говорит:

> embrace change.

Continuous Integration:

> integrate constantly.

Lean:

> learn before irreversible decisions.

Evolutionary Architecture:

> keep architecture adaptable.

DORA:

> improve feedback, throughput and stability together.

SRE:

> production evidence beats optimism.

Stable Baselines со всем этим прекрасно уживаются.

Они добавляют одно довольно неприятное требование:

> **Назови точно, что уже доказано в этом конкретном состоянии системы. И не используй более сильное слово, пока не получил более сильное доказательство.**

SIB0 разрешает сказать:

> форма зафиксирована.

SIB1:

> форма реализована.

SIB2:

> реализация доказанно интегрирована.

RC:

> конкретное продуктовое наполнение готово стать релизом.

Release:

> мы действительно это выпустили.

Возможно, поэтому модель так естественно выросла из практики нескольких реальных проектов. Она почти не говорит разработчику, **как писать код**.

Она говорит, **когда разрешено сделать следующее более сильное утверждение о готовности этого кода**.

И это приводит к формуле, которую я бы оставил последней строкой статьи:

> **Stable Baseline - это не стабильность как отсутствие изменений. Это доказанное право безопасно продолжать изменения.**

---

# Источники к реальным интерлюдиям и упомянутым школам

[^ariane]: European Space Agency, *Ariane 501 - Presentation of Inquiry Board report*, 23 July 1996: https://www.esa.int/Newsroom/Press_Releases/Ariane_501_-_Presentation_of_Inquiry_Board_report

[^knight]: U.S. Securities and Exchange Commission, Knight Capital order / enforcement materials. SEC описывает неполный deployment на один из восьми серверов, активацию dormant Power Peg code и итоговый loss свыше $460 млн: https://www.sec.gov/Archives/edgar/data/1569391/000119312513401173/d613486dex101.htm и https://www.sec.gov/newsroom/press-releases/2013-222

[^mco]: NASA, *Mars Climate Orbiter* и NASA Software Engineering Handbook о failure to translate English units to metric и недостаточном V&V ground software: https://science.nasa.gov/mission/mars-climate-orbiter/ и https://swehb.nasa.gov/spaces/7150/pages/16449723/SWE-017%2B-%2BProject%2Band%2BSoftware%2BTraining

[^gitlab]: GitLab, *Postmortem of database outage of January 31*, 10 February 2017, и incident summary: https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/ и https://about.gitlab.com/blog/gitlab-dot-com-database-incident/

[^crowdstrike]: CrowdStrike, *Preliminary Post Incident Review: Content Configuration Update Impacting the Falcon Sensor and the Windows Operating System*, 24 July 2024: https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/

[^agile]: *Manifesto for Agile Software Development - Principles*: https://agilemanifesto.org/principles

[^ci]: Martin Fowler, *Continuous Integration*: https://martinfowler.com/articles/continuousIntegration.html

[^runway]: Scaled Agile Framework, *Architectural Runway*: https://framework.scaledagile.com/architectural-runway
