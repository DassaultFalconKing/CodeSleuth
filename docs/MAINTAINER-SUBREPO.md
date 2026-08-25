# Maintainer Guide: standalone pack repository and project submodule

This guide describes the recommended ownership model for the review pack:

```text
standalone GitHub repository
        ↓ pinned Git submodule
project/tools/opencode-repo-review-pack
        ↓ installer
project/.opencode
```

The standalone pack repository is the source of truth for pack development.
Each project pins a specific pack commit through a Git submodule. The installer
copies the managed runtime into the project's `.opencode/` directory so normal
OpenCode use does not depend on symlinks or on the submodule being on `PATH`.

This gives two separate guarantees:

1. **source reproducibility**: the project records the exact pack commit through
   its submodule pointer;
2. **installed-runtime reproducibility**: the project can commit the resulting
   `.opencode` policy/agents/tools/configuration.

## 1. Export the current pack from Aleph_Rugent

The pack currently lives under:

```text
opencode-repo-review-pack/
```

on the development branch.

From the root of `Aleph_Rugent`:

```bash
git switch tooling/opencode-repo-review-pack

git subtree split \
  --prefix=opencode-repo-review-pack \
  -b export/opencode-repo-review-pack
```

The resulting branch has the pack directory as its repository root.

Inspect it before publishing:

```bash
git ls-tree -r --name-only export/opencode-repo-review-pack | less
```

The root should contain files such as:

```text
README.md
VERSION
install.py
install.sh
install.ps1
review-pack
review-pack.ps1
pack/
profiles/
docs/
tests/
```

## 2. Create the standalone GitHub repository

Using GitHub CLI:

```bash
gh repo create DassaultFalconKing/opencode-repo-review-pack \
  --private \
  --description "Portable evidence-first OpenCode repository review and documentation pack"
```

Push the split branch as the new repository's `main`:

```bash
git push \
  git@github.com:DassaultFalconKing/opencode-repo-review-pack.git \
  export/opencode-repo-review-pack:main
```

Then clone the new repository independently:

```bash
cd ..
git clone git@github.com:DassaultFalconKing/opencode-repo-review-pack.git
cd opencode-repo-review-pack
```

From this point onward, develop the pack in the standalone repository. Do not
continue treating the copy nested inside `Aleph_Rugent` as canonical.

## 3. Establish the standalone repository baseline

Recommended initial checks:

```bash
cat VERSION
python3 tests/test_lifecycle.py
```

Also inspect that the pack source contains:

```text
.gitignore
README.md
docs/USER-GUIDE.md
docs/MAINTAINER-SUBREPO.md
```

Tag the first standalone release after validation, for example:

```bash
git tag -a v0.2.0 -m "OpenCode review pack v0.2.0"
git push origin main --tags
```

The `VERSION` file remains the distribution version. A behavior-changing pack
release should bump it before tagging.

## 4. Add the pack to a project as a Git submodule

From the target project root:

```bash
git submodule add \
  git@github.com:DassaultFalconKing/opencode-repo-review-pack.git \
  tools/opencode-repo-review-pack
```

Then initialize/update it explicitly:

```bash
git submodule update --init --recursive
```

Commit the submodule contract:

```bash
git add .gitmodules tools/opencode-repo-review-pack
git commit -m "chore: add OpenCode review pack submodule"
```

The project now pins the exact pack commit.

For a fresh clone of the project, use either:

```bash
git clone --recurse-submodules <PROJECT-URL>
```

or:

```bash
git clone <PROJECT-URL>
cd <PROJECT>
git submodule update --init --recursive
```

## 5. Install from the pinned submodule into the project

Recommended interactive flow:

```bash
./tools/opencode-repo-review-pack/review-pack .
```

PowerShell:

```powershell
.\tools\opencode-repo-review-pack\review-pack.ps1 .
```

Choose the requested project profile, permissions, Exa/web behavior, watchdog,
and compaction policy in the TUI, then apply.

For non-interactive installation:

```bash
./tools/opencode-repo-review-pack/install.sh .
```

PowerShell:

```powershell
.\tools\opencode-repo-review-pack\install.ps1 .
```

Validate immediately:

```bash
python3 .opencode/bin/review-pack-smoke.py .
```

## 6. Commit the installed project contract

After reviewing the TUI selections and smoke result, commit the authored
installation:

```bash
git add .opencode

git status --short
```

Before committing, confirm that `.opencode/state/`, cache/log/runtime artifacts,
and Python `__pycache__` files are not staged.

Recommended project commit:

```bash
git commit -m "chore(opencode): install repository review environment"
```

The important distinction is:

```text
tools/opencode-repo-review-pack/   source package, pinned submodule
.opencode/                         installed project-specific runtime contract
.opencode/state/                   local ephemeral state, never committed
```

## 7. Recommended update model: pinned and reproducible

For projects that care about reproducibility, the **submodule commit is the
source authority**.

Do not let the installed target-local updater silently outrun the submodule
pointer.

Update in two explicit steps.

### Step 1: advance the submodule intentionally

```bash
cd tools/opencode-repo-review-pack
git fetch origin
git checkout main
git pull --ff-only
cd ../..
```

Or choose a specific release tag:

```bash
cd tools/opencode-repo-review-pack
git fetch --tags origin
git checkout v0.3.0
cd ../..
```

Record the new submodule pointer:

```bash
git add tools/opencode-repo-review-pack
```

### Step 2: update the installed `.opencode` from that exact checkout

```bash
./tools/opencode-repo-review-pack/install.sh . --update
```

PowerShell:

```powershell
.\tools\opencode-repo-review-pack\install.ps1 . --update
```

Then:

```bash
python3 .opencode/bin/review-pack-smoke.py .
git status --short
```

Review all `.opencode` changes and update conflicts before committing.

Commit both the submodule pointer and installed runtime in the same project
change when practical:

```bash
git add tools/opencode-repo-review-pack .opencode
git commit -m "chore(opencode): update review pack"
```

This makes the project state auditable: the source pack revision and installed
runtime move together.

## 8. Floating self-update mode

The installed command:

```bash
.opencode/bin/review-pack-update
```

can update directly from the recorded upstream `remote/ref`.

This is convenient for personal/workstation use, but it can make the installed
`.opencode` newer than the project's pinned submodule pointer.

Therefore use one of these governance modes deliberately:

### Reproducible project mode (recommended)

```text
submodule commit = authority
→ update submodule
→ install.sh . --update
→ smoke
→ commit submodule + .opencode together
```

### Floating workstation mode

```text
installed updater follows recorded upstream branch/tag
→ convenient latest pack
→ submodule pointer may lag
```

Do not mix the modes accidentally.

## 9. Detached HEAD in submodules

Git submodules commonly checkout a detached commit. The pack records the exact
source commit regardless. When possible, the installer also resolves
`refs/remotes/origin/HEAD` so update metadata can identify the upstream default
branch.

The exact commit remains the reproducibility anchor. A branch/ref is only needed
for floating self-update discovery.

## 10. Release process for the standalone pack repository

Recommended release sequence:

```text
change pack
→ bump VERSION
→ update docs when user-visible behavior changes
→ run lifecycle tests
→ install into disposable fixture
→ run target smoke
→ commit
→ tag
→ push main + tag
```

Example:

```bash
printf '0.3.0\n' > VERSION
python3 tests/test_lifecycle.py

git add VERSION README.md docs pack install.py tests
git commit -m "release: review pack 0.3.0"
git tag -a v0.3.0 -m "OpenCode review pack v0.3.0"
git push origin main v0.3.0
```

Do not tag a release solely because files exist. The release gate is the
lifecycle behavior: install, settings persistence, smoke, update safety, and
legacy adoption.

## 11. Keeping Aleph_Rugent clean after extraction

Once the standalone repository becomes canonical, remove the duplicated source
directory from the Aleph feature branch or replace it with the submodule.

Recommended end state:

```text
Aleph_Rugent/
├── .gitmodules
├── tools/
│   └── opencode-repo-review-pack/   # submodule
└── .opencode/                       # installed Aleph-specific review environment
```

Do not keep two editable canonical copies of the pack. That creates version
ambiguity faster than any updater can repair it.

## 12. Optional: use `git subtree` instead of submodule

A subtree is appropriate when consumers must receive pack source without
submodule commands. It trades simpler cloning for less explicit source pinning
and more cumbersome upstream synchronization.

Add as subtree:

```bash
git subtree add \
  --prefix=tools/opencode-repo-review-pack \
  git@github.com:DassaultFalconKing/opencode-repo-review-pack.git \
  main \
  --squash
```

Update:

```bash
git subtree pull \
  --prefix=tools/opencode-repo-review-pack \
  git@github.com:DassaultFalconKing/opencode-repo-review-pack.git \
  main \
  --squash
```

For this project, **submodule is the recommended default** because the exact pack
revision should remain visible as a first-class dependency and because pack
source and installed `.opencode` have intentionally separate lifecycles.
