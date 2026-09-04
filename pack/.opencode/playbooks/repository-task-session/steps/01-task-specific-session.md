Ты продолжаешь работу с уже исследованным репозиторием.

Это TASK-SPECIFIC SESSION.

Перед началом:

1. re-resolve current HEAD/branch;
2. прочитай последний CodeSleuth discovery/full-review report;
3. проверь, что его target HEAD и scope всё ещё применимы;
4. если HEAD изменился, сделай delta review между report baseline и current HEAD;
5. re-resolve submodule gitlinks;
6. не переносить assumptions из predecessor report на изменённые файлы без проверки.

Authority hierarchy для этой сессии:

1. executable evidence;
2. current tracked source/config;
3. exact-pinned external/submodule source;
4. current contracts/docs;
5. prior CodeSleuth findings;
6. review inference.

Текущая задача:

<TASK>

Не анализируй весь проект заново без необходимости.

Сначала установи affected components и evidence closure задачи:
- какие файлы непосредственно участвуют;
- какие callers/callees;
- какие configs/contracts;
- какие tests/gates;
- какие external/submodule dependencies.

После этого выполни task-specific review или implementation.

Все выводы классифицируй как:
VERIFIED
EXECUTED
INFERRED
BLOCKED
UNKNOWN

Не утверждай PASS без реально выполненной проверки.

В итоговом отчёте укажи:
- baseline HEAD;
- current HEAD;
- submodule SHAs;
- использованные authority documents;
- affected files/components;
- findings/changes;
- tests actually run;
- remaining unknowns;
- exact resulting HEAD, если были изменения.
