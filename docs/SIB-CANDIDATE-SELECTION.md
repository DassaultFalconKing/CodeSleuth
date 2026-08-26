# SIB candidate selection from the release stream

## Status

This document is a **normative selection contract** for choosing future
SIB0/SIB1/SIB2 candidates in CodeSleuth.

It complements:

- [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md);
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md);
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md);
- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md).

## Canonical candidate stream

For a numbered release `X.Y.Z`, the only normal source from which a future SIB
candidate is selected is:

```text
dev/release-X.Y.Z
```

For the current release line this is:

```text
dev/release-0.4.0
```

The branch is a **mutable integration/candidate stream**. It is not itself a SIB
and it is not accepted in the abstract.

A SIB candidate is the **literal exact commit SHA at the head of that release
stream at the moment maintainers select it for EHA**.

Canonical rule:

> **The release branch supplies candidates; the exact SHA carries the proof.**

## Selection operation

Candidate selection is conceptually:

```text
dev/release-X.Y.Z
        |
        | capture literal branch HEAD
        v
exact SHA A
        |
        | start EHA campaign bound to A
        v
SIB0 / SIB1 / SIB2 evidence for A
```

Selection does not mutate or freeze the release branch. It freezes only the
**identity of the EHA target**.

At selection time record at minimum:

- release branch name;
- literal `git rev-parse HEAD` / remote ref SHA;
- selected full SHA;
- branch/dirty state for the test checkout;
- EHA campaign ID;
- selection timestamp in durable evidence/reporting.

The selected SHA must be reachable as the literal release-branch head at the
selection point. A PR head, repair branch, synthetic PR merge ref, tree-equivalent
commit, or nearby ancestor is not a substitute.

## Branch movement during EHA

`dev/release-X.Y.Z` may continue moving after SHA `A` was selected.

That does **not** change the running EHA campaign:

```text
selection time:    dev/release-X.Y.Z -> A
EHA target:                             A

later:             dev/release-X.Y.Z -> B
EHA target:                             A
```

Evidence already being produced remains evidence for `A` only.

If maintainers now want `B` to become the SIB instead, start a new campaign on
`B`. Do not retarget the old campaign and do not transfer `A`'s verdicts.

A convenience branch/tag may point at a selected SHA for navigation, but it is
not acceptance identity and must never replace the exact SHA recorded in the
EHA ledger.

## Repair-loop integration rule

An EHA repair branch is **not** directly promoted as the next SIB candidate.

The repair loop is:

```text
release-head A selected
        |
        v
EHA FAIL on A
        |
        v
fix/eha-* branch from A
        |
        | minimal repair + regression + focused tests
        v
repair commit R
        |
        | integrate through normal release-stream discipline
        v
dev/release-X.Y.Z -> exact integration head B
        |
        v
new EHA campaign on B
```

`R` may be useful repair evidence, but the next SIB candidate is `B`, the exact
resulting release-stream head after the repair is integrated.

This rule prevents a repair branch from becoming a second competing integration
line and ensures the SIB proof applies to the composition from which release
work will actually continue.

If integration creates a merge commit, that merge commit is the new candidate.
Tree equality with the repair commit does not transfer evidence to the merge
commit.

## Candidate versus SIB

A selected release-head SHA is only a **candidate**.

It becomes claimable only through the normal EHA rules:

```text
SIB0 = SIB0 PASS on selected exact SHA
SIB1 = SIB0 PASS + SIB1 PASS on selected exact SHA
SIB2 = SIB0 PASS + SIB1 PASS + SIB2 PASS on selected exact SHA
```

Ordinary CI, a release-branch name, a PR approval, or an older accepted commit
cannot manufacture those claims.

## Promotion rule

When an exact release-stream candidate passes the required EHA profile:

1. retain the exact selected SHA in the durable EHA ledger;
2. record the appropriate SIB claimability for that SHA;
3. if a convenience SIB ref/tag is maintained, point it to that exact SHA;
4. do not rewrite the accepted SHA when the release branch later advances;
5. treat any later release-head as a new candidate requiring fresh evidence for
   any SIB claim made about it.

For SIB2 specifically, release construction may continue from the accepted
exact SIB2 SHA. If `dev/release-X.Y.Z` has already advanced beyond it while EHA
was running, maintainers must deliberately decide whether to continue from the
accepted SIB2 state or establish fresh SIB2 evidence for the newer release head.
The newer descendant does not inherit SIB2.

## Why this policy exists

Without one candidate stream, it is easy to accumulate:

- a release branch;
- an EHA branch;
- a repair branch;
- a PR head;
- a merge commit;
- several tree-equivalent SHAs;

and then quietly test one while promoting another.

CodeSleuth therefore chooses one normal composition stream and one immutable
proof identity:

> **Compose on `dev/release-X.Y.Z`; select its literal HEAD; prove that SHA; repair back through the release stream; select again.**
