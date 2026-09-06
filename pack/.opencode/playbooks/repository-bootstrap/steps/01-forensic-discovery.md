# Step 1 — identify target and build inventory

Treat the target as an unknown folder containing some software project. Do not infer product, language, architecture, build system, or authority from the folder name, README title, or one conspicuous file.

Work read-only. Do not modify tracked files, Git refs, branches, tags, submodules, lockfiles, dependency state, generated artifacts, or caches. Do not install dependencies merely to make discovery easier.

Classify claims as:

- VERIFIED_SOURCE — directly supported by file or Git metadata;
- EXECUTABLE_EVIDENCE — supported by a check actually executed;
- REVIEW_INFERENCE — derived from multiple verified facts;
- UNVERIFIED_EXTERNAL — depends on an external repository, binary, or service not yet inspected;
- UNKNOWN — evidence is insufficient.

First establish target identity:

- whether the folder is a Git worktree;
- repository root when applicable;
- current branch or detached HEAD;
- exact HEAD SHA;
- dirty and untracked state;
- remotes and upstream tracking;
- submodules and exact gitlink SHAs;
- nested repositories;
- worktrees;
- relevant tags.

If the target is not a Git repository, record that explicitly and continue as filesystem/codebase discovery. Never create or move refs.

Then build a bounded inventory:

- file count and top-level directories;
- languages and extensions;
- build/config files and package manifests;
- lockfiles;
- tests and CI workflows;
- scripts and docs;
- examples;
- generated/vendor/build/cache directories;
- binary artifacts;
- model/data assets;
- submodules and external source trees.

Classify major directories as SOURCE, TEST, DOCS, CONFIG, BUILD, GENERATED, VENDOR, CACHE, DATA/MODELS, or UNKNOWN. Keep vendor/generated/cache out of architecture conclusions unless they are materially required.

Output `identity_inventory` containing the exact identity, bounded inventory, classification decisions, and unresolved UNKNOWN items needed by the next Step.
