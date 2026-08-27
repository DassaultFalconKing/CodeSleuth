# Bug Hunter — host-tracked repo catalog refit (PR #77 onto 2d62781) — anti-pattern audit

- date: 2026-08-27T22:28Z
- target: 389b1d9fc4f140e5ec2d55dd59c9303398ff0954
- dirty: yes — `?? .opencode/` (worktree-local pack materialization, ignored via .git/info/exclude, not tracked)
- scope: `fix/pr77-refit-host-catalog-2d62781` vs `dev/release-0.4.0@2d62781f70bbf079a84afcb8c429e8d8c5e87413` — Semantic Refit of PR #77 host catalog (FR-LIFE-004/005) onto release stream; 10 files changed, 564+/53-
- agent: OpenCode build (primary controller)
- reviewId: none (read-only Bug Hunter review; no durable review_state checkpoint created)
- ehaCampaignId: none (not an EHA campaign; exact-head acceptance still governed by docs/EXACT-HEAD-ACCEPTANCE.md)

## Summary

Независимый Bug Hunter аудит exact HEAD `389b1d9` (branch `fix/pr77-refit-host-catalog-2d62781`, один коммит поверх `dev/release-0.4.0@2d62781`) — Semantic Refit исторической ветки PR #77 в текущую архитектуру. Проверены 10 error-pattern классов EP-01..EP-10 как целые классы, не только diff. HEAD корректно закрывает BLOCKER 1 (exact commit всегда виден в каталоге) и BLOCKER 2 (prune только missing, не degraded) для FR-LIFE-004/005, но оставляет один HIGH EP-02: деградированный metadata/origin при `reachable==True` стирает prior exact commit из registry, нарушая retain-prior-identity. Full suite `python -m pytest -q` = 263 passed, 6 skipped, `ruff check` pass — визуальный TUI gate требует отдельного `CODESLEUTH_UI_VISUAL_REGRESSION=1` job и не покрыт default pytest (EP-05 green-by-skip). До HIGH fix promotion в release stream небезопасен.

## EHA / SIB status

Not an EHA report — no eha.ndjson campaign bound.

- exact target SHA: `389b1d9fc4f140e5ec2d55dd59c9303398ff0954` (`git rev-parse HEAD`)
- SIB0: PENDING — claimable: no — SIB0 inventory frozen (`docs/SIB0-CAPABILITY-INVENTORY.md:1`, 11 classes) но не re-proven на этом SHA; EHA вердикт не записан
- SIB1: PENDING — claimable: no — implementations for `codesleuth.install-lifecycle` существуют, но SIB1 не re-proven
- SIB2: PENDING — claimable: no — composition `cc -r` не проходила exact-head EHA на `389b1d9`
- blocker finding IDs: none (эта проверка не EHA FAIL, а Bug Hunter findings)
- predecessor campaign: none interrogated
- successor campaign: none

SIB lineage: current `origin/SIB` = `2b0044cb61a698b31d179e59cc486990d217b134` (merge promote final semantic-refit), `origin/main` = `1bdf78a564b6a505e600480c01c27666a77d5cc6` (divergent), `dev/release-0.4.0` = `2d62781f70bbf079a84afcb8c429e8d8c5e87413` — merge-base HEAD vs dev/release-0.4.0 = `2d62781`.

## Findings

### HIGH: EP-02 — degraded metadata/origin collapsed into absence, стирает prior exact commit при reachable==True

- location: `pack/.opencode/bin/codesleuth_project/tracked_repos.py:181-194` (`_installed_metadata`), `216-264` (`_probe_entry`), `282-332` (`list_tracked_repositories`/`record_tracked_repository`); дубликат `.opencode/bin/codesleuth_project/tracked_repos.py:181-332` (identical blob 759b51ba)
- evidence: `_installed_metadata` ловит `OSError`/`JSONDecodeError`/`RuntimeError` (invalid state от `codesleuth_naming._read_object`) и возвращает `None` (186-193). `_probe_entry` при `path.is_dir()==True` и `lifecycle_state` успехе ставит `reachable=True`, но `source=None`, `version=None` (246-249). `list_tracked_repositories:307-310` ветка `if live.get("reachable"): entry.update(live)` перезаписывает предыдущий `source/version/origin/name` значением `None` без сохранения prior. В `record_tracked_repository:352-358` сохранение prior только при `if not live.get("reachable")`. Воспроизведено исполнением: запись repo с `codesleuth.json` commit `abc123def...` → порча файла `"{ malformed"` → `list_tracked_repositories(refresh=True)` → `listed[0]["source"] is None`, `version is None` (ожидалось retain `abc123`). Аналогично `git remote remove origin` при `reachable==True` → `origin` перезаписывается `None`, `name` падает с `example/repo` на `repo` (проверено).
- recommendation: в обеих функциях при `reachable==True` не перезаписывать `source/version/name/origin/lifecycle` значением `None` — сохранять предыдущие non-None как в `reachable==False` ветке. Или различать `no file` vs `unreadable` в `_installed_metadata` и маркировать degraded.
- violated FR: `FR-LIFE-004` (commit always visible), `FR-LIFE-005` (retain prior identity)

### MEDIUM: EP-03 — default-contract inversion для list_tracked prune

- location: `pack/.opencode/bin/codesleuth_project/tracked_repos.py:282-306` (`prune_missing`), `pack/.opencode/bin/codesleuth_project/__init__.py:679-681` (`--list`), `docs/PROJECT-LIFECYCLE.md:74`, `docs/LLM-OPERATOR.md:104-109`
- evidence: BASE `dev/release-0.4.0` (`git show dev/release-0.4.0:tracked_repos.py:81-130`) — `list_tracked_repositories(refresh=True)` всегда хранил missing paths. HEAD — `prune_missing=None -> prune_missing=refresh`, `if prune_missing and live.get("exists")==False: continue` (304-306) → `refresh=True` теперь дропает missing. Старый caller `codesleuth_project --list` (делает `list_tracked_repositories(refresh=True)`) без нового флага получит урезанный список. Фикс намеренный для FR-LIFE-004 ("keeps deleted test/install paths as version-only rows" must_not), но меняет наблюдаемый return shape без версионирования.
- recommendation: зафиксировать breaking change явно (CHANGELOG + FR-LIFE-004 proof) или сделать default `prune_missing=False` и требовать явный opt-in. Минимально — задокументировать inversion.
- violated principle: EP-03 — `новый optional flag не считается backward compatible, если старому caller пришлось бы передавать флаг`

### MEDIUM: EP-05 — green by skip / visual gate не в default pytest

- location: `tests/test_tui_visual_regression.py:20-23` (`skipif CODESLEUTH_UI_VISUAL_REGRESSION != "1"`), `.github/workflows/acceptance.yml:53-86` (job tui-visual), `tests/test_tui_visual_regression_contract.py:40-53`
- evidence: `python -m pytest -q` → `263 passed, 6 skipped` (проверено). 6 skipped — это 5 visual тестов. Claim в commit message `Gates: 263 passed` цитирует только default suite; артефакты `screen.svg/ui.log/events.log/analysis.json` не генерируются локально. Canonical SIB2 требует отдельный `tui-visual` job (`acceptance.yml:53`, `TUI-VISUAL-REGRESSION.md`), но разработчик, запустивший `pytest`+`ruff`, получит green без visual. `tests/test_tui_visual_regression_contract.py` проверяет наличие `CODESLEUTH_UI_VISUAL_REGRESSION` в workflow, но не то что default job не покрывает visual.
- recommendation: указывать `263 passed, 6 skipped (visual requires CODESLEUTH_UI_VISUAL_REGRESSION=1, proven in tui-visual job)`; для release-acceptance требовать `bun run test` + `python -m pytest` + отдельный `CODESLEUTH_UI_VISUAL_REGRESSION=1` прогон.
- violated FR: `FR-TUI-002`, `FR-TUI-004` acceptance gap

### LOW: EP-06 — ambient git/python без pinned path

- location: `pack/.opencode/bin/codesleuth_project/tracked_repos.py:82-91` (`_git_output ["git", "-C", ...]`), `pack/.opencode/bin/codesleuth_tui.py:819-838`, `install.py:43-65` (`MIN_GIT_VERSION=(2,35,0)`), `install.sh:5-8`
- evidence: все git вызовы через ambient PATH; `tracked_repos` не проверяет версию и молча вернёт `None`/`reachable=False` при отсутствии git. Installer требует `git>=2.35`, но catalog достаточно любого git — не material для этого diff. 40+ вхождений `["git",` консистентны.
- recommendation: нет (документировать что catalog требует любой git).

### LOW: EP-01/EP-09 — short_remote/display truncation hardening

- location: `pack/.opencode/bin/codesleuth_project/tracked_repos.py:94-118` (`short_remote`), `121-155` (`source_label`)
- evidence: `short_remote("https://gitlab.com/group/sub/repo.git")` тест допускает `group/repo` OR `sub/repo` (`test_short_remote_variants:144`) — spec неоднозначен, но exact identity (`source.remote` full SHA) хранится в registry, display показывает `short@ref#commit` (7-char) — mutable/display не вытесняет authority. Full SHA persisted, label short — compliant. Нет места где branch/ref используется вместо commit как authority ( `install.py:158-167` пишет `branch --show-current` как `ref` наряду с `commit` — commit остаётся authority, detached HEAD `ref=None`).
- recommendation: уточнить spec для GitLab nested groups (возвращать последние 2 сегмента) и зафиксировать.

## Paths inspected

- `pack/.opencode/bin/codesleuth_project/tracked_repos.py:1-386` — catalog core, short_remote, source_label, format_tracked_label, probe, list/record/forget
- `.opencode/bin/codesleuth_project/tracked_repos.py:1-386` — duplicate installed copy (identical)
- `pack/.opencode/bin/codesleuth_project/__init__.py:1-757` — lifecycle, CLI --list/--forget, record_tracked_repository call sites
- `pack/.opencode/bin/codesleuth_project/paths.py:1-592` — reports INDEX, git info/exclude
- `pack/.opencode/bin/codesleuth_tui.py:605-614` (`_tracked_select_options`), `672-681` (track), `840-903` (status)
- `install.py:149-171` (source_metadata), `355-376` (self-install guard)
- `pack/.opencode/bin/codesleuth_naming.py:1-66` (resolve_state_file, fail_on_conflict)
- `pack/.opencode/codesleuth-naming.json:1-87` (canonical vs legacy state names)
- `docs/protected-capabilities.json:272-365` (codesleuth.install-lifecycle, FR-LIFE-004/005)
- `docs/PROJECT-LIFECYCLE.md:74-101`, `docs/LLM-OPERATOR.md:94-109`, `docs/SIB0-CAPABILITY-INVENTORY.md:70-146`
- `docs/CODESLEUTH-PRODUCT-CONTRACT.md:1`, `AGENTS.md:1-362`, `CONTRIBUTING.md:1-164`
- `.github/workflows/acceptance.yml:1-102` (exact-head CODESLEUTH_ACCEPTANCE_SHA)
- `tests/test_tracked_repos.py:1-344` (14 tests, все green), `tests/conftest.py:1-22` (host isolation), `tests/test_tui_visual_regression.py:20-23` (skipif), `tests/test_tui_visual_regression_contract.py:1-97`, `package.json:1-17`, `pyproject.toml:1-10`
- `git` history: `git rev-parse HEAD` 389b1d9, `git show dev/release-0.4.0:tracked_repos.py`, `git diff dev/release-0.4.0 HEAD --stat`

## Checks run

- `git rev-parse HEAD` — `389b1d9fc4f140e5ec2d55dd59c9303398ff0954` — pass
- `git rev-parse --abbrev-ref HEAD` — `fix/pr77-refit-host-catalog-2d62781` — pass
- `git log --oneline -5` — 389b1d9 fix(catalog): target-native refit ... onto 2d62781 — pass
- `git diff dev/release-0.4.0 HEAD -- docs/protected-capabilities.json` — FR-LIFE-004/005 added — pass
- `git diff dev/release-0.4.0 HEAD --stat` — 10 files, 564+/53- — pass
- `python -m pytest tests/test_tracked_repos.py -v` — 14 passed — pass
- `python -m pytest -q` — 263 passed, 6 skipped in 97.93s — pass (visual skipped)
- `python -m ruff check .` — All checks passed! — pass
- `python -m pytest tests/test_naming_cutover.py -v` — 6 passed — pass
- `python -m pytest tests/test_project_lifecycle.py` (subspace) — 20 passed — pass (sample)
- `python -c` reproduction degraded metadata → source None (BUG confirmed) — fail (witness for HIGH)
- `python -c` reproduction git remote remove → origin None (PARTIAL) — fail
- `python scripts/contributor_antipatterns.py scan --strict` — not found (scanner missing) — not run
- `bun run test` / `bun tests/*_smoke.ts` — not run in this Bug Hunter pass (durability not touched)

Not run: `ruff format --check`, Textual viewport pilots, live eha_github_bridge, full bun matrix.

## Recommendations

- Закрыть HIGH EP-02 перед promotion: в `list_tracked_repositories` и `record_tracked_repository` при `reachable==True` не перезаписывать `source/version/name/origin` значением `None`; сохранять prior non-None. Добавить regression тесты: malformed `codesleuth.json` при prior valid source → retain commit; `git remote get-url` transient fail при reachable → retain origin/name.
- Уточнить EP-03 contract: либо версионировать prune_missing breaking change (CHANGELOG), либо default `prune_missing=False`. Добавить тесты для обоих режимов prune.
- Для release-acceptance указывать `263 passed, 6 skipped (visual отделен)` и гонять `CODESLEUTH_UI_VISUAL_REGRESSION=1` job; не считать `pytest -q` достаточным для SIB2.
- Сохранить `SIB` на `origin/SIB 2b0044c` до успешной exact-head EHA нового release head; не форсировать promotion `389b1d9` до HIGH fix + fresh EHA.
- Следующему implementation-agent: взять этот ledger как вход, сделать минимальный delta в `tracked_repos.py:307-325` и `335-370`, прогнать `python -m pytest` + `ruff` + targeted reproduction, затем интегрировать fix через `dev/release-0.4.0` → новый literal HEAD → новый EHA campaign с SIB0.

## Limitations

- Bounded Bug Hunter, не full SIB0/SIB1/SIB2 EHA — no `eha_state_*` verdicts recorded, no durable reviewId.
- Не inspected полные `pack/.opencode/bin/review_pack_tui*.py` воркеры line-by-line, `codesleuth_mcp/server.py` глубоко, и `install.py` three-way merge — sampled via grep.
- Scanner `scripts/contributor_antipatterns.py` отсутствует — аудит manual.
- Report локальный (` .codesleuth/reports/` через `.git/info/exclude`), может содержать source excerpts — sanitize перед `git add -f`.
- Dirty flag `?? .opencode/` — точный HEAD `389b1d9` чист, но worktree имеет untracked pack materialization; EHA freeze требует `dirty:false`.
