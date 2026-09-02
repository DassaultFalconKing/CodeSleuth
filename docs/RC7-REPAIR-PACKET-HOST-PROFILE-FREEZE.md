# RC7 MF5 — RepairPacketV1 / HostExecutionProfileV1 Freeze

**Status:** FROZEN RC7 MICRO-CONTRACT  
**Session:** MF5  
**Branch:** `docs/rc7-freeze-repair-packet`  
**Scope:** semantic repair packet, host execution profile, semantic-operation-to-command boundary, and Jinja rendering identity  
**Implementation:** explicitly out of scope; this commit is documentation only

## 1. Freeze verdict

This document freezes the W11 semantic/execution/rendering boundary closely enough that an implementation does not need to invent policy, command-selection, scope, target, executable, quoting, or renderer semantics.

The central contract is:

```text
validated repair semantics
        |
        v
RepairPacketV1
        + HostExecutionProfileV1
        |
        v
HostExecutionPreflightV1
        |
        v
RepairCommandCompilerV1
        |
        +--> CommandPlanV1: raw argv / structured host call
        |
        v
CommandPresentationV1
        |
        v
RepairRenderModelV1
        |
        v
trusted Jinja renderer
        |
        v
derived host-facing instructions only
```

Execution MUST consume `CommandPlanV1` or the corresponding structured host call. Execution MUST NOT consume a command string assembled by Jinja.

Jinja is therefore presentation, not a hidden command compiler and not a policy engine.

---

## 2. Exact inputs

The session re-resolved the supplied refs before freezing this contract.

| Input | Exact identity | Disposition |
| --- | --- | --- |
| runtime branch | `feature/rc6-eha-brownfield-bootstrap` | executable evidence only |
| runtime HEAD | `1de37c75251a1e0d9904cffdb82695e92e3fab23` | unchanged from triage |
| runtime tree | `5e8acd831d4f64e2f4a9fcba5dd875b918d55c89` | inspected for current surfaces/templates |
| planning branch | `docs/rc7-ledger-authority-repair-plan` | design input |
| planning HEAD | `86218a51345fafb47d0ffec543773846a70ac76a` | unchanged from triage |
| planning tree | `ab7f937e6c615d920761f7b67156d36514186ed3` | design input tree |
| pinned review / antithesis | `be5d158880f649ecb568d9a505c694e87bd76e0e` | review input, not authority |
| frozen thesis commit | `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218` | thesis input, not implementation authority |
| frozen thesis blob | `0f46825308454d9c8d0b3d0b48a2cdcc7845e120` | exact thesis document identity |
| synthesis blob | `a3556ca3bd84546835a3ff66847cfb03da54fc7b` | design input |
| repair/render planning blob | `21a63da327d21f79263d57b09c96eda0d8c28fe7` | accepted planning input |
| multirenderer planning blob | `44f400f9ee7daeb11c48833bc5ac3a8e9951762c` | accepted planning input, narrowed by synthesis |
| runtime export contract blob | `c18d10a92f7bfc6df1181769349aaf1320c00c69` | current compatibility evidence |
| runtime GitHub EHA bridge doc blob | `3d5d4b64d820434c01b040dd8ff09f030ae686d0` | current compatibility evidence |
| runtime EHA repair-loop doc blob | `16bbff3c812127e87fb24a3705cda41ac7f8c4d3` | current normative compatibility evidence |
| runtime OpenCode config blob | `25f0cf1fc6541d3d84239ef832fe292a9fbf4fc8` | host-permission evidence |
| runtime GitHub bridge core blob | `49b8632f5e11c5a7324a63ce095fbabb7371b06e` | executable host-boundary evidence |

The planning branch did not advance beyond the supplied planning baseline. No later planning commit therefore needed adjudication against the MF5 freeze question.

### 2.1 Existing Jinja inventory

The exact runtime tree at `1de37c75251a1e0d9904cffdb82695e92e3fab23` contains no tracked `.jinja`, `.jinja2`, or `.j2` template files and no tracked path containing `jinja`.

Therefore MF5 is not constrained by a pre-existing Jinja template ABI. W11 may introduce trusted templates later, but only under the contract frozen here.

### 2.2 Preserved upstream invariants

This freeze preserves, rather than redefines, these stronger existing rules:

1. tracked Git/current project state remains source authority;
2. `findings.ndjson` / amendments remain finding-domain history authority;
3. the implementation ledger, when implemented, owns accepted-plan execution history only;
4. existing `eha.ndjson` remains EHA campaign/verdict authority and evolves in place;
5. a failed exact SHA remains failed for the claim/profile that failed;
6. repair creates a new source subject and requires fresh acceptance;
7. host output is not repository-state or EHA authority;
8. post-mutation state is established by re-observation, not by process exit or model prose;
9. reports, Mermaid, exports, Jinja output and other projections remain derived/non-authoritative;
10. host permissions remain fail-closed and may be stricter than any repair profile.

---

## 3. Authority and ownership

### 3.1 `RepairPacketV1`

`RepairPacketV1` is a validated, content-addressed **workflow object** describing what repair operation has already been authorized and bounded by upstream repair policy.

It is not:

- source authority;
- EHA authority;
- acceptance-policy authority;
- permission to expand scope;
- a shell script;
- a hidden replacement for `EhaRepairCaseV1` or `LedgerRecoveryCaseV1`.

### 3.2 `HostExecutionProfileV1`

`HostExecutionProfileV1` is a validated, content-addressed **execution binding** describing how one host can realize already-selected semantic operations.

It owns no project truth. It MUST NOT make a forbidden repair permissible. It MAY narrow what can execute on a host, but it MUST NOT widen packet scope or host permissions.

### 3.3 `CommandPlanV1`

`CommandPlanV1` is a deterministic derived execution plan. It contains raw argv tokens or a structured host-tool call. It is not an authority record.

### 3.4 Jinja output

Jinja output has:

```text
projectionAuthority = none
roundTripCapability = RENDER_ONLY
```

It is a host-facing representation of the same validated packet/plan. It MUST NOT be parsed back as repair authority.

---

## 4. Shared scalar/reference types

The following structural types are part of MF5 because leaving them implicit would move identity decisions into implementation.

### 4.1 `StableRefV1`

```text
StableRefV1 {
  domain:
    GIT
    | FINDING
    | IMPLEMENTATION
    | EHA
    | PROJECT_POLICY
    | ACCEPTANCE_SNAPSHOT
    | EXTERNAL_EVIDENCE
    | EHA_REPAIR_CASE
    | LEDGER_RECOVERY_CASE
  id: non-empty UTF-8 string
  digestSha256?: 64 lowercase hex characters
}
```

Rules:

1. `id` is an opaque canonical identity copied from the owning domain.
2. MF5 MUST NOT normalize, shorten, rerank, reinterpret, or regenerate another domain's ID.
3. `digestSha256`, when present, binds the referenced bytes/semantic object according to that owning domain's digest contract. MF5 does not redefine the upstream digest.
4. Two refs are equal only when `domain`, `id`, and present digest values are equal.

### 4.2 `SemanticValueV1`

```text
SemanticValueV1 =
  STRING(value)
  | INTEGER(value)
  | BOOLEAN(value)
  | PATH(value)
  | REF(StableRefV1)
  | STRING_LIST(values[])
  | PATH_LIST(values[])
  | REF_LIST(values[])
```

No arbitrary executable code, template expression, or shell fragment is a semantic value type.

### 4.3 Canonical JSON and hashes

For MF5-owned content identities:

```text
canonicalBytes = UTF-8(RFC 8785 JSON Canonicalization Scheme(object))
digest = lowercase-hex(SHA-256(canonicalBytes))
```

Set-valued arrays defined by this document MUST be lexicographically sorted by their canonical JSON bytes and MUST contain no duplicates before hashing. Ordered arrays explicitly described as `steps[]` or `argv[]` preserve order.

Volatile timestamps and rendered text are not part of `RepairPacketV1` or `HostExecutionProfileV1` semantic identity.

---

## 5. `RepairPacketV1` frozen schema

```text
RepairPacketV1 {
  schemaVersion: "RepairPacketV1"
  repairPacketId: "repair-packet-v1:" + packetDigest
  packetDigest: 64 lowercase hex characters

  repairCaseRef: StableRefV1
  target: TargetIdentityV1

  failureRefs: StableRefV1[]
  obligationRefs: StableRefV1[]

  intendedOperation: SemanticOperationV1
  mutationScope: MutationScopeV1

  requiredPreconditions: PredicateV1[]
  expectedPostconditions: PredicateV1[]

  evidenceRefs: StableRefV1[]
  prohibitedOperations: ProhibitionV1[]

  executionProfileRef: HostExecutionProfileRefV1

  assumptions: string[]
  limitations: string[]
  residualUncertainty: string[]
  stopConditions: string[]
}
```

### 5.1 Packet identity

`packetDigest` is computed over all fields above **except** `repairPacketId` and `packetDigest` themselves.

```text
repairPacketId = "repair-packet-v1:" + packetDigest
```

Any semantic change to target, references, operation, scope, conditions, evidence, prohibitions, execution-profile reference, assumptions, limitations, uncertainty, or stop conditions creates a new packet identity.

### 5.2 Repair case identity

`repairCaseRef.domain` MUST be exactly one of:

```text
EHA_REPAIR_CASE
LEDGER_RECOVERY_CASE
```

The owning domain decides whether a case is admissible and whether a packet may be issued. MF5 only preserves the exact reference.

### 5.3 `TargetIdentityV1`

```text
TargetIdentityV1 =
  GitTargetV1 {
    kind: "GIT_COMMIT"
    repositoryId: non-empty string
    commitSha: 40 lowercase hexadecimal characters
  }

  | DomainGenerationTargetV1 {
    kind: "DOMAIN_GENERATION"
    domain: FINDING | IMPLEMENTATION | EHA
    generationRef: StableRefV1
    generationDigestSha256: 64 lowercase hex characters
  }
```

Rules:

- Git source repair MUST use an exact 40-character commit SHA, never a branch name as target identity.
- A branch/worktree name is navigation metadata and MUST NOT replace exact target identity.
- Ledger recovery MUST retain the owning domain generation reference and digest; MF5 MUST NOT choose which generation becomes authoritative.

### 5.4 Failure, obligation and evidence references

`failureRefs`, `obligationRefs`, and `evidenceRefs` are set-valued arrays.

They MUST:

- contain at least one failure reference for a repair packet;
- contain at least one obligation reference when the repair is driven by a declared acceptance/contract obligation;
- retain upstream canonical identities;
- remain references rather than copied pseudo-authority.

A bounded evidence excerpt MAY be carried later in a render model for usability, but the material truth link remains `evidenceRefs`.

### 5.5 `SemanticOperationV1`

```text
SemanticOperationV1 {
  operationId: non-empty internal/adopted semantic operation identifier
  operationRevision: positive integer
  arguments: SemanticArgumentV1[]
  steps: SemanticStepV1[]
}

SemanticArgumentV1 {
  name: /^[A-Za-z][A-Za-z0-9_.-]*$/
  value: SemanticValueV1
}

SemanticStepV1 {
  stepId: non-empty string
  actionId: non-empty semantic action identifier
  arguments: SemanticArgumentV1[]
}
```

Rules:

1. `operationId`, `actionId`, argument meaning, and step order are semantic data selected before host rendering.
2. `steps[]` is ordered.
3. Argument names MUST be unique within one argument list.
4. A string argument is data. It MUST NOT be treated as a shell fragment.
5. A host profile may bind an action to a tool, but MUST NOT replace `actionId` with a different semantic action.

### 5.6 `MutationScopeV1`

```text
MutationScopeV1 =
  RepositoryMutationScopeV1 {
    kind: "REPOSITORY_PATHS"
    rootTarget: GitTargetV1
    allowedPathGlobs: normalized repository-relative POSIX globs[]
    forbiddenPathGlobs: normalized repository-relative POSIX globs[]
    allowedMutationKinds: CREATE | MODIFY | DELETE | RENAME []
    maxChangedPaths: positive integer
  }

  | DomainMutationScopeV1 {
    kind: "DOMAIN_OBJECTS"
    domain: FINDING | IMPLEMENTATION | EHA
    allowedObjectRefs: StableRefV1[]
    prohibitedObjectRefs: StableRefV1[]
    maxMutatedObjects: positive integer
  }
```

Repository path rules:

- paths/globs are repository-relative and use `/` as canonical separator;
- absolute paths, drive-qualified paths, NUL, and any `..` path segment are invalid;
- `allowedPathGlobs` MUST be non-empty;
- `forbiddenPathGlobs` wins over `allowedPathGlobs` on overlap;
- no implied `**` exists; broad scope must be explicit;
- mutation outside the validated scope is a hard stop, not a reason to widen scope.

### 5.7 `PredicateV1`

```text
PredicateV1 {
  predicateId: non-empty string
  oracleId: non-empty static/internal oracle identifier
  arguments: SemanticArgumentV1[]
  expectedResult: "PASS"
  evidenceRefs: StableRefV1[]
}
```

A required precondition or expected postcondition MUST name a deterministic oracle. Free-form prose alone is not executable predicate semantics.

A human explanation MAY be rendered, but it cannot replace `oracleId` and typed arguments.

### 5.8 `ProhibitionV1`

```text
ProhibitionV1 {
  kind:
    OPERATION_ID
    | ACTION_ID
    | TOOL_ID
    | EXECUTION_FAMILY
    | MUTATION_KIND
    | PATH_GLOB
    | NETWORK_DESTINATION
  value: non-empty string
  authorityRef?: StableRefV1
}
```

`prohibitedOperations` is semantic policy data. Jinja MUST NOT hide, remove, reinterpret, or override it.

### 5.9 `HostExecutionProfileRefV1`

```text
HostExecutionProfileRefV1 {
  hostProfileId: "host-execution-profile-v1:" + profileDigest
  profileDigest: 64 lowercase hexadecimal characters
}
```

A packet is bound to one exact execution profile identity. Rendering the same packet for a materially different host profile requires a new packet identity because `executionProfileRef` changes.

This is deliberate: host execution assumptions are material repair inputs, not decorative metadata.

---

## 6. `HostExecutionProfileV1` frozen schema

```text
HostExecutionProfileV1 {
  schemaVersion: "HostExecutionProfileV1"
  hostProfileId: "host-execution-profile-v1:" + profileDigest
  profileDigest: 64 lowercase hex characters

  hostFamily: CURSOR | CODEX | OPENCODE | HUMAN
  hostVersionIdentity: non-empty string

  platform: PlatformIdentityV1
  shell: ShellIdentityV1
  tools: ToolIdentityV1[]

  worktree: WorktreeBindingV1
  cwdRelative: normalized repository-relative POSIX path

  environmentBindings: EnvironmentBindingV1[]
  allowedExecutionFamilies: ExecutionFamilyV1[]
  commandMappings: CommandMappingV1[]

  quotingPolicyId: QuotingPolicyIdV1
  executionConstraints: ExecutionConstraintsV1
  networkPolicy: NetworkPolicyV1
}
```

`profileDigest` is computed over all fields except `hostProfileId` and `profileDigest`.

```text
hostProfileId = "host-execution-profile-v1:" + profileDigest
```

### 6.1 `PlatformIdentityV1`

```text
PlatformIdentityV1 {
  os: LINUX | MACOS | WINDOWS
  osVersionIdentity: non-empty string
  archIdentity: non-empty string
}
```

Platform identity is actual host identity for this profile, not prose such as `desktop-ish` or `Windows-compatible`.

### 6.2 `ShellIdentityV1`

```text
ShellIdentityV1 =
  { kind: "NONE", executableToolId: null }
  | { kind: "POSIX_SH", executableToolId: ToolIdentityV1.toolId }
  | { kind: "POWERSHELL", executableToolId: ToolIdentityV1.toolId }
```

Allowed combinations in V1:

```text
LINUX   -> NONE | POSIX_SH
MACOS   -> NONE | POSIX_SH
WINDOWS -> NONE | POWERSHELL
```

`cmd.exe` command-string construction is not part of V1.

The presence of a shell identity does **not** authorize arbitrary shell-string execution.

### 6.3 `ToolIdentityV1`

```text
ToolIdentityV1 {
  toolId: non-empty stable profile-local identifier
  kind: EXECUTABLE | TRUSTED_WRAPPER | HOST_TOOL

  executablePath?: absolute host path
  versionIdentity?: non-empty string
  executableSha256?: 64 lowercase hexadecimal characters

  hostToolName?: non-empty string
}
```

Rules:

1. `EXECUTABLE` and `TRUSTED_WRAPPER` require an absolute `executablePath` after profile resolution.
2. Ambient `PATH` lookup is permitted only while constructing/validating a profile. The frozen profile and `CommandPlanV1` MUST store/use the resolved absolute executable identity.
3. At least one of `versionIdentity` or `executableSha256` MUST be present for an external executable/wrapper.
4. `HOST_TOOL` requires `hostToolName` and has no executable path.
5. A renderer MUST NOT choose one tool among alternatives.

This is compatible with the existing Mermaid export correctness discipline, which already fails closed when exact executable/runtime identities are unavailable.

### 6.4 `WorktreeBindingV1`

```text
WorktreeBindingV1 {
  worktreeRef: StableRefV1
  rootAbsolutePath: absolute host path
  expectedTarget: TargetIdentityV1
}
```

For Git repair:

```text
expectedTarget.kind == GIT_COMMIT
```

and preflight MUST prove that the bound worktree currently represents the exact target required by the packet before mutation.

`cwdRelative`:

- MUST be normalized;
- MUST NOT be absolute;
- MUST NOT contain `..`;
- resolves below `rootAbsolutePath` only.

### 6.5 `EnvironmentBindingV1`

```text
EnvironmentBindingV1 {
  bindingId: non-empty string
  name: /^[A-Za-z_][A-Za-z0-9_]*$/
  source:
    LITERAL { value: string }
    | HOST_ENV { sourceName: string }
    | SECRET_REF { ref: non-empty opaque secret reference }
  required: boolean
  exposure: PUBLIC | SECRET
}
```

Rules:

- secret values MUST NOT be serialized into `RepairPacketV1`, `HostExecutionProfileV1`, render manifests, or Jinja output;
- `SECRET_REF` stores only the opaque locator;
- a required unresolved binding fails preflight;
- Jinja receives redacted metadata for `SECRET` bindings, never the resolved value.

### 6.6 `ExecutionFamilyV1`

V1 is deliberately closed:

```text
DIRECT_ARGV
TRUSTED_WRAPPER_ARGV
HOST_TOOL
```

V1 intentionally has no `SHELL_STRING`, `EVAL`, or `TEMPLATE_COMMAND` execution family.

Compound shell behavior must be represented as multiple semantic steps or delegated to a versioned trusted wrapper whose identity is in the profile.

### 6.7 `CommandMappingV1`

```text
CommandMappingV1 =
  ProcessMappingV1 {
    actionId: non-empty string
    executionFamily: DIRECT_ARGV | TRUSTED_WRAPPER_ARGV
    toolId: ToolIdentityV1.toolId
    argvTemplate: ArgvTemplateItemV1[]
    requiredEnvironmentBindingIds: string[]
    requiresNetwork: boolean
  }

  | HostToolMappingV1 {
    actionId: non-empty string
    executionFamily: HOST_TOOL
    toolId: ToolIdentityV1.toolId
    hostArgumentMap: HostArgumentMapItemV1[]
    requiredEnvironmentBindingIds: string[]
    requiresNetwork: boolean
  }
```

For one `HostExecutionProfileV1`, `actionId` MUST be unique. Zero mappings or more than one mapping for a requested `actionId` is an error.

`ArgvTemplateItemV1` is one of:

```text
LITERAL(value)
ARG(name)
ARG_LIST(name)
```

Expansion rules:

- `LITERAL` emits exactly one argv token and contains no template syntax;
- `ARG` emits exactly one token from the named semantic argument;
- `ARG_LIST` emits one token per list element, preserving list order;
- no substring interpolation exists;
- no token is split on whitespace;
- no shell metacharacter has execution meaning at this layer.

A substantive flag such as `--force`, `--delete`, `--no-verify`, `--network`, a changed test selector, or a changed target may appear only if it is already frozen in the validated `CommandMappingV1` or represented by an explicit semantic argument. Jinja cannot add it.

### 6.8 `ExecutionConstraintsV1`

```text
ExecutionConstraintsV1 {
  timeoutMs: positive integer
  maxOutputBytes?: positive integer
  maxResidentMemoryBytes?: positive integer
  maxChildProcesses?: non-negative integer
}
```

`timeoutMs` is normative and mandatory for every process-backed operation.

Optional resource keys mean only that MF5 adds no additional bound for that resource; the host's own baseline limits still apply and may be stricter.

No profile may disable a stricter host watchdog, permission rule, sandbox, or process limit.

### 6.9 `NetworkPolicyV1`

```text
NetworkPolicyV1 =
  { mode: "DENY", allowlist: [] }
  | { mode: "ALLOWLIST", allowlist: NetworkDestinationV1[] }

NetworkDestinationV1 {
  scheme: https | ssh
  host: exact DNS name or IP literal
  port: integer 1..65535
}
```

Rules:

- wildcards are forbidden in V1;
- unrestricted network mode does not exist in V1;
- `requiresNetwork=true` with `mode=DENY` fails preflight;
- the host may be stricter than the profile;
- profile network permission never overrides repository/host policy.

---

## 7. Command construction boundary

### 7.1 Exact owner

The only MF5 layer allowed to transform semantic repair actions into executable process tokens is:

```text
RepairCommandCompilerV1
```

It consumes:

```text
RepairPacketV1
HostExecutionProfileV1
validated host/worktree observation
```

and emits:

```text
CommandPlanV1
```

Jinja is downstream of this compiler.

### 7.2 `HostExecutionPreflightV1`

Preflight is fail-closed and MUST complete before an automated mutation command may execute.

It deterministically checks:

1. packet schema and packet content identity;
2. profile schema and profile content identity;
3. exact packet `executionProfileRef` == supplied profile identity;
4. exact target/worktree identity;
5. normalized cwd remains inside the worktree root;
6. all required precondition oracles return PASS;
7. every semantic `actionId` has exactly one command mapping;
8. every selected execution family is listed in `allowedExecutionFamilies`;
9. every selected tool has a resolved exact identity and exists on the host;
10. required environment bindings resolve without exposing secrets;
11. operation/mapping does not violate `prohibitedOperations`;
12. declared mutation effects remain within `mutationScope`;
13. network requirement is compatible with `networkPolicy`;
14. host baseline permission is at least as restrictive as required; effective permission is the intersection of packet, profile, and host policy.

If any check is not provably satisfied, preflight fails. There is no optimistic default.

### 7.3 `CommandPlanV1`

```text
CommandPlanV1 {
  schemaVersion: "CommandPlanV1"
  repairPacketId: RepairPacketV1.repairPacketId
  hostProfileId: HostExecutionProfileV1.hostProfileId
  target: TargetIdentityV1
  commands: CommandInvocationV1[]
}

CommandInvocationV1 =
  ProcessInvocationV1 {
    commandId: non-empty string
    stepId: SemanticStepV1.stepId
    executionFamily: DIRECT_ARGV | TRUSTED_WRAPPER_ARGV
    toolId: ToolIdentityV1.toolId
    executablePath: absolute path
    argv: string[]
    cwdAbsolutePath: absolute path under worktree root
    environmentBindingIds: string[]
    timeoutMs: positive integer
    networkPolicy: NetworkPolicyV1
  }

  | HostToolInvocationV1 {
    commandId: non-empty string
    stepId: SemanticStepV1.stepId
    executionFamily: HOST_TOOL
    toolId: ToolIdentityV1.toolId
    hostToolName: string
    arguments: canonical structured arguments
    environmentBindingIds: string[]
    timeoutMs: positive integer
    networkPolicy: NetworkPolicyV1
  }
```

`argv` contains raw tokens. It is never a single shell command string.

### 7.4 Deterministic compiler algorithm

For each ordered `SemanticStepV1`:

```text
1. lookup exactly one CommandMappingV1 by actionId
2. require mapping.executionFamily in profile.allowedExecutionFamilies
3. require mapped tool exists and exact identity validates
4. require no packet prohibition matches action/tool/family/network/mutation
5. validate semantic argument names/types against mapping references
6. expand argv items token-by-token; never interpolate substrings
7. normalize any PATH/PATH_LIST semantic values
8. prove mutation-relevant paths are within packet mutationScope
9. resolve cwd below bound worktree root
10. bind environment by binding ID, preserving secret redaction
11. apply profile timeout/network/resource constraints
12. emit one CommandInvocationV1
```

If the mapping is `HOST_TOOL`, step 6 is replaced by deterministic field-to-field construction of the structured host argument object. It still may not consult Jinja.

### 7.5 Execution rule

Automated execution MUST invoke the process API with:

```text
executablePath
argv[]
cwdAbsolutePath
environment
```

or invoke the exact structured host tool with its structured arguments.

It MUST NOT execute:

```text
renderedCommandText
Jinja output
Markdown code fences
operator-facing copy/paste text
```

as authority-bearing input.

This matches the current GitHub EHA bridge's established use of process argv and separate host permission policy rather than rendering a shell program and hoping punctuation remains benevolent.

---

## 8. Quoting and escaping policy

Quoting in MF5 is presentation-only. It has no effect on the argv passed to execution.

### 8.1 Frozen policy IDs

```text
CODESLEUTH_ARGV_JSON_V1
CODESLEUTH_POSIX_SH_DISPLAY_V1
CODESLEUTH_POWERSHELL_DISPLAY_V1
```

A profile MUST select exactly one `quotingPolicyId` compatible with its shell identity.

Compatibility:

```text
shell NONE       -> CODESLEUTH_ARGV_JSON_V1
shell POSIX_SH   -> CODESLEUTH_POSIX_SH_DISPLAY_V1
shell POWERSHELL -> CODESLEUTH_POWERSHELL_DISPLAY_V1
```

### 8.2 `CODESLEUTH_ARGV_JSON_V1`

Presentation is the RFC 8785 canonical JSON array:

```text
[executablePath, ...argv]
```

No claim is made that this string can be pasted into a shell.

### 8.3 `CODESLEUTH_POSIX_SH_DISPLAY_V1`

For each token, including executable path:

```text
if token == "":
    output "''"
else if token matches ^[A-Za-z0-9_@%+=:,./-]+$:
    output token unchanged
else:
    wrap token in single quotes
    replace each embedded ' with '"'"'
```

Join tokens with one ASCII space.

This is a copy/paste representation only. Execution still uses raw argv.

### 8.4 `CODESLEUTH_POWERSHELL_DISPLAY_V1`

Render:

```text
& '<executable>' '<arg1>' '<arg2>' ...
```

For every token:

1. wrap the whole token in single quotes;
2. replace every embedded single quote `'` with two single quotes `''`;
3. perform no `$`, backtick, semicolon, pipe, parenthesis, wildcard, or subexpression interpretation inside the quoted token.

Again, this is presentation only.

### 8.5 `CommandPresentationV1`

```text
CommandPresentationV1 {
  commandId: CommandInvocationV1.commandId
  quotingPolicyId: QuotingPolicyIdV1
  displayText: deterministic presentation string
}
```

`CommandPresentationV1` is produced before Jinja.

Jinja MAY place `displayText` in prose/code blocks and MAY choose whitespace around it. Jinja MUST NOT rebuild quoting from raw argv.

---

## 9. Jinja renderer contract

### 9.1 Static/internal registry

RC7 MF5 follows the synthesis decision that the renderer registry is static/internal for RC7.

Arbitrary repository-provided Jinja code, extensions, Python helpers, custom filters, or runtime-loaded render plugins are not part of W11.

### 9.2 Frozen renderer identity

Canonical renderer descriptor:

```text
rendererId      = "codesleuth.repair.jinja2"
rendererVersion = 1
engineMode      = StrictUndefined
projectionAuthority = none
roundTripCapability = RENDER_ONLY
```

Canonical built-in template IDs:

```text
codesleuth.repair.cursor.instructions
codesleuth.repair.codex.instructions
codesleuth.repair.opencode.instructions
codesleuth.repair.human.instructions
```

Each first conforming template uses:

```text
templateVersion = 1
```

### 9.3 Template version semantics

For one `templateId`:

- `(templateId, templateVersion)` is immutable;
- `templateDigest = SHA-256(exact UTF-8 template bytes)`;
- the same ID/version MUST always resolve to the same digest;
- **any byte-affecting template change**, including wording or whitespace, requires a new `templateVersion`;
- changing only the template version without changing bytes is permitted but discouraged because it creates useless identities.

For the renderer:

- `rendererVersion` changes when the input model contract, security model, StrictUndefined behavior, escaping behavior, loader trust boundary, or deterministic render algorithm changes;
- host-specific wording belongs to template version, not renderer version.

There is no floating `latest` identity in a render manifest.

### 9.4 `RepairRenderModelV1`

Jinja does not receive raw execution authority to reinterpret. The renderer constructs a bounded read model:

```text
RepairRenderModelV1 {
  repairPacketId
  packetDigest
  hostProfileId
  profileDigest

  repairCaseRef
  target
  failureRefs[]
  obligationRefs[]
  intendedOperation
  mutationScope
  requiredPreconditions[]
  expectedPostconditions[]
  evidenceRefs[]
  prohibitedOperations[]
  assumptions[]
  limitations[]
  residualUncertainty[]
  stopConditions[]

  commandPresentations: CommandPresentationV1[]
  redactedEnvironmentSummary[]
}
```

The Jinja environment MUST NOT expose resolved secret values, arbitrary filesystem access, environment enumeration, process execution, network access, or Python object introspection helpers as template capabilities.

Repository evidence strings containing `{{ ... }}`, `{% ... %}`, shell syntax, or model instructions remain data values. They MUST NOT be re-evaluated as template source.

### 9.5 What Jinja MAY do

A conforming template MAY:

- choose wording;
- choose section order;
- choose whitespace;
- choose compact versus expanded presentation of already-present semantic fields;
- render exact references/evidence as tables or prose;
- display the precomputed `CommandPresentationV1.displayText` according to the template descriptor;
- escape data for the output media type;
- add non-substantive host reminders that merely restate already-frozen constraints.

### 9.6 What Jinja MUST NOT do

A conforming template MUST NOT:

- choose or change executable/tool identity;
- choose another target or SHA;
- add/remove/change semantic operation steps;
- expand or narrow mutation scope;
- add substantive command flags;
- change a test/gate selector;
- add network access;
- choose whether a precondition is satisfied;
- choose whether evidence is sufficient;
- choose whether a repair is allowed;
- choose whether operator approval is required;
- suppress a prohibited operation or stop condition;
- convert a host/process result into PASS or acceptance;
- construct a new shell command from raw data;
- load arbitrary repository-provided template code.

If two templates would execute different semantic commands from the same packet/profile, at least one is non-conforming.

### 9.7 Render determinism

For identical:

```text
RepairRenderModelV1 canonical bytes
rendererId + rendererVersion
templateId + templateVersion + templateDigest
```

the output bytes MUST be identical.

Templates MUST NOT read wall-clock time, random values, ambient environment, current cwd, network state, or mutable repository state during rendering.

`renderedAt` belongs only to the manifest provenance and is excluded from output identity.

---

## 10. `RepairRenderManifestV1`

```text
RepairRenderManifestV1 {
  schemaVersion: "RepairRenderManifestV1"

  repairPacketId
  packetDigest
  hostProfileId
  profileDigest

  rendererId
  rendererVersion
  templateId
  templateVersion
  templateDigestSha256
  quotingPolicyId

  outputDigestSha256
  renderedAt

  projectionAuthority: "none"
  roundTripCapability: "RENDER_ONLY"
}
```

The manifest proves provenance of a derived render. It is not repair permission, source evidence, or EHA acceptance evidence.

---

## 11. Effective permission rule

A `RepairPacketV1` and `HostExecutionProfileV1` can only narrow execution. They cannot grant capabilities the host does not already allow.

Effective permission is:

```text
packet permits
AND profile maps/allows
AND host baseline permits
```

If any operand is false or unknown:

```text
DENY / STOP
```

There is no `profile overrides host` path.

In particular, the current GitHub EHA bridge is a read-only acceptance adapter with a fail-closed shell allowlist and strict candidate-cleanliness checks. A W11 repair packet MUST NOT turn that EHA testing session into a mutation session. Repair remains a separate role/host action producing a new exact candidate.

---

## 12. Ambiguity and error behavior

MF5 errors are fail-closed. No error below permits `best effort`, default shell selection, PATH fallback at execution time, scope expansion, or template inference.

Canonical error codes:

```text
PACKET_SCHEMA_INVALID
PACKET_IDENTITY_MISMATCH
PROFILE_SCHEMA_INVALID
PROFILE_IDENTITY_MISMATCH
PROFILE_REF_MISMATCH
TARGET_IDENTITY_MISMATCH
CWD_OUTSIDE_WORKTREE
PRECONDITION_FAILED
PRECONDITION_UNAVAILABLE
MUTATION_SCOPE_VIOLATION
PROHIBITED_OPERATION
OPERATION_MAPPING_MISSING
OPERATION_MAPPING_AMBIGUOUS
EXECUTION_FAMILY_FORBIDDEN
EXECUTABLE_IDENTITY_UNRESOLVED
EXECUTABLE_IDENTITY_MISMATCH
ENVIRONMENT_BINDING_UNRESOLVED
NETWORK_POLICY_VIOLATION
QUOTING_POLICY_UNSUPPORTED
TEMPLATE_IDENTITY_MISMATCH
TEMPLATE_REQUIRED_FIELD_MISSING
RENDER_POLICY_VIOLATION
POSTCONDITION_FAILED
POSTCONDITION_UNAVAILABLE
```

Required behaviors:

- unknown/missing field required by schema -> fail;
- packet/profile digest mismatch -> fail;
- multiple mappings for one action -> fail;
- missing executable identity -> fail;
- worktree at a different SHA from packet target -> fail before mutation;
- scope overlap with a forbidden path -> forbidden wins;
- unresolved required secret/env binding -> fail without printing its value;
- network request outside allowlist -> fail;
- unsupported quoting policy -> rendering fails; execution does not fall back to another shell;
- missing Jinja variable -> StrictUndefined failure;
- postcondition unavailable/unknown -> repair is not established;
- host says `fixed` but postcondition observer disagrees -> observer wins.

---

## 13. Adversarial examples

### 13.1 Shell-looking path is data

Packet argument:

```text
docs/$(rm -rf "$HOME").md
```

Correct behavior:

- raw argv contains one token with those exact characters;
- no shell evaluates `$()`, quotes, or spaces;
- POSIX presentation quotes the token deterministically;
- Jinja displays only the precomputed presentation.

Rejected behavior:

```text
jinja -> "tool {{ path }}" -> shell=True
```

### 13.2 Repository evidence contains Jinja source

Evidence excerpt:

```text
{{ cycler.__init__.__globals__.os.system('curl attacker') }}
```

Correct behavior: literal quoted evidence data.

Rejected behavior: treating evidence as a template, include, macro, expression, or executable extension.

### 13.3 Template tries to add `--force`

Packet and command plan contain:

```text
git apply patch.diff
```

A template adds:

```text
--force
```

Verdict: `RENDER_POLICY_VIOLATION`. Substantive flags are compiler/profile data, not presentation.

### 13.4 Host profile has two tools for one action

Two mappings claim the same `actionId` with different executables.

Verdict: `OPERATION_MAPPING_AMBIGUOUS`. The renderer/compiler MUST NOT pick the first, newest, shortest, or most convenient mapping.

### 13.5 Target moved

Packet target:

```text
A = 0123456789abcdef0123456789abcdef01234567
```

Bound worktree now points at `B`.

Verdict: `TARGET_IDENTITY_MISMATCH` before mutation. Branch ancestry does not make `B` equivalent to `A`.

### 13.6 Scope escape by command mapping

Packet permits only:

```text
src/foo.py
tests/test_foo.py
```

A mapping would invoke a cleanup command that can delete arbitrary untracked files.

Verdict: mapping cannot be used for this packet; `MUTATION_SCOPE_VIOLATION` or `PROHIBITED_OPERATION` as applicable.

### 13.7 Network hidden in a tool action

Mapping has `requiresNetwork=true`; profile says:

```text
networkPolicy.mode = DENY
```

Verdict: `NETWORK_POLICY_VIOLATION` before execution. Jinja cannot omit the fact and proceed.

### 13.8 Windows injection-looking argument

Argument:

```text
a'b; Remove-Item -Recurse C:\
```

Execution uses one raw argv token. PowerShell presentation doubles the embedded single quote and single-quotes the whole token. The semicolon has no command-separator meaning inside that representation and no execution meaning in raw argv.

### 13.9 Jinja hides a stop condition

Packet contains:

```text
SCOPE_EXPANSION_REQUIRED
```

A template condition suppresses the stop section.

Verdict: non-conforming template / `RENDER_POLICY_VIOLATION`. Required material semantics cannot be conditionally erased.

### 13.10 Host output claims success with zero effective delta

Host returns success text but re-observation sees no required state change.

Verdict: postcondition not established. Existing repair semantics remain unchanged: host prose and exit status are not source authority.

---

## 14. Compatibility obligations

An implementation of W11 MUST preserve all of the following.

### 14.1 EHA / repair lifecycle

- EHA campaigns do not mutate their own exact target.
- Failed exact SHAs remain historical failures.
- Repair produces a new exact candidate.
- Every SIB degree claimed for the new candidate requires fresh evidence.
- Focused repair checks may qualify a candidate for EHA but do not replace EHA.

### 14.2 GitHub EHA bridge

- the bridge remains a control-plane adapter, not a second EHA implementation;
- the exact candidate stays read-only except for already sanctioned external report/state surfaces;
- fail-closed shell permissions remain effective;
- W11 profiles do not weaken bridge permissions or cleanliness postconditions;
- durable `eha.ndjson` remains verdict/completion authority.

### 14.3 Existing renderer/export authority

- current reports/exports/Mermaid remain derived;
- `exportAuthority: none` / retained-artifact semantics are not weakened;
- exact executable/runtime identity discipline remains compatible;
- missing exact runtime identity fails closed rather than falling back to ambient execution.

### 14.4 Cross-host parity

The same packet semantics may be represented for Cursor, Codex, OpenCode, or a human. Host wording differs; these fields may not differ without a new packet identity:

- repair case identity;
- target identity;
- failure/obligation refs;
- intended operation;
- bounded mutation scope;
- required preconditions;
- expected postconditions;
- evidence refs;
- prohibited operations;
- execution-profile reference.

A different execution profile creates a different packet identity because host execution assumptions are material.

### 14.5 Host policy intersection

Current OpenCode policy uses explicit ask/allow/deny surfaces, and the trusted GitHub EHA bridge narrows them further with a deny-by-default shell allowlist. W11 MUST compose with those constraints by intersection, not by replacement.

---

## 15. MUST / MUST NOT summary

### MUST

- validate typed packet/profile data before rendering;
- bind packet to exact repair case and exact target;
- bind packet to an exact content-addressed host profile;
- represent bounded mutation scope explicitly;
- keep preconditions/postconditions machine-addressable through deterministic oracle IDs;
- resolve exact executable/tool identity before command construction;
- use only `DIRECT_ARGV`, `TRUSTED_WRAPPER_ARGV`, or `HOST_TOOL` execution families in V1;
- construct raw argv/structured calls before Jinja;
- use deterministic quoting presentation IDs;
- use StrictUndefined-equivalent template evaluation;
- keep repository/evidence strings as data;
- record renderer/template identities and digests;
- fail closed on missing/ambiguous mappings or identities;
- re-observe postconditions after host mutation;
- preserve existing host restrictions and stronger policy.

### MUST NOT

- let Jinja choose executable/tool identity;
- let Jinja choose or change target SHA;
- let Jinja add substantive flags or remove required commands;
- let Jinja expand mutation scope;
- let Jinja make policy/acceptance decisions;
- execute Jinja output as an authority-bearing shell string;
- use `shell=True`/eval-equivalent command strings as the V1 execution contract;
- use ambient PATH lookup at execution after profile resolution;
- serialize secret values into packet/profile/render artifacts;
- silently fall back to another shell or quoting policy;
- treat a branch name as exact source identity;
- treat host success prose/exit `0` as proof of repaired repository state;
- let a profile grant permission denied by host or packet policy;
- load arbitrary project Jinja extensions/code in RC7 W11.

---

## 16. Explicit non-goals

MF5 / W11 does **not** define or implement:

1. when `EhaRepairCaseV1` or `LedgerRecoveryCaseV1` is authorized to produce a packet; that remains with the owning domain/policy;
2. W9 attempt-budget, cycle-detection, or repair-loop convergence semantics;
3. W10 source-repair versus ledger-recovery authority permissions;
4. W14 full JSON/NDJSON/Markdown/Jinja/Mermaid parity implementation;
5. a generic shell programming language;
6. arbitrary `cmd.exe` command-string support;
7. arbitrary repository-provided Jinja plugins/templates/extensions;
8. a renderer marketplace or runtime plugin loader;
9. automatic tool installation, update, dependency resolution, or PATH mutation;
10. a new supervisor/runtime/controller for CodeSleuth;
11. a new evidence, finding, implementation, or EHA authority;
12. automatic scope expansion or architecture reopening;
13. secret management beyond carrying opaque secret references;
14. promotion of host output, rendered text, or repair learning into project authority.

---

## 17. Downstream workstreams unlocked

This freeze directly unlocks:

```text
W11 RepairPacketV1 schema implementation
W11 HostExecutionProfileV1 schema implementation
W11 host execution preflight
W11 semantic-operation -> CommandPlan compiler
W11 deterministic command presentation
W11 trusted static Jinja rendering
W11 renderer/template provenance manifest
W11 cross-host semantic parity fixtures for the frozen fields
```

It is a prerequisite for:

```text
W14 rendering parity
```

W14 can now compare Jinja output against the same typed source object without allowing the renderer to redefine commands.

---

## 18. Unresolved items

**No unresolved MF5 semantic decision remains that W11 implementation must invent.**

The following are upstream/downstream dependencies, not holes in this freeze:

- W9 determines repair attempt/convergence policy and supplies stop-state data;
- W10 determines which repair-case domain may authorize which mutation class;
- domain authorities define their own stable reference identities/digests;
- concrete repair policies define the operation/action IDs that a host profile binds;
- W14 later proves cross-renderer parity using these frozen semantics.

W11 implementation may consume those identities/policies as inputs. It MUST NOT redefine them.

---

## 19. Freeze statement

The resolved boundary is:

```text
RepairPacketV1
    = WHAT has already been authorized and bounded

HostExecutionProfileV1
    = WHICH exact host/tool/cwd/env/execution bindings may realize it

RepairCommandCompilerV1
    = HOW semantic actions become raw argv / structured host calls

CommandPresentationV1
    = deterministic copy/paste/documentation representation

Jinja
    = wording / ordering / whitespace / escaped presentation only

Host
    = execution authority within existing permissions

Postcondition observer
    = establishes what repository/domain state actually resulted
```

No template may cross upward across that boundary.

FREEZE STATUS:
FROZEN

UNLOCKS:
W11 RepairPacket / HostExecutionProfile / Jinja rendering

PREREQUISITE FOR:
W14 rendering parity
