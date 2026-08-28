import {
  Button,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  Pill,
  Row,
  Stack,
  Table,
  Text,
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

const RECIPES = [
  {
    title: "1. Repository architecture + correctness",
    body: "/repo-review map the repository architecture, identify authority boundaries and invariants, then perform an in-depth correctness review. Inspect callers, callees, tests, CI, migrations and documentation, not only obvious entrypoints. Record exact evidence for every material finding.",
  },
  {
    title: "2. Current branch acceptance",
    body: "/repo-review compare current HEAD and worktree against the repository's canonical base branch. Review changed code and unchanged consumers/contracts/tests/CI. Distinguish blockers from improvements and state all unreviewed areas.",
  },
  {
    title: "3. Documentation truth pass",
    body: "/repo-docs build an evidence-first repository guide from current source, manifests, CI and tests. Separate documented guarantees from behavior inferred from code and call out stale or contradictory documentation.",
  },
  {
    title: "4. Persist an assistant-readable report",
    body: "/repo-report write a CodeSleuth analytical report for the current HEAD and active review into .codesleuth/reports/, update INDEX.md, and keep application source unchanged.",
  },
  {
    title: "5. External assumptions verification",
    body: "/repo-review identify version-sensitive external API, framework and tooling assumptions in this repository. Use websearch only for discovery and webfetch primary official sources for verification. Do not claim web verification without successful tool calls.",
  },
] as const;

export default function PlaybooksCurrentScreen() {
  const [view, setView] = useCanvasState<"home" | "modal">(
    "playbooks-view",
    "modal",
  );

  return (
    <Stack gap={20}>
      <Stack gap={8}>
        <H1>Current Playbooks control</H1>
        <Text tone="secondary">
          Live capture from `CodeSleuthApp` at 120×35. The Home button
          `#playbooks` pushes `CodeSleuthPlaybookScreen`, a modal over
          `PromptScreen` — not the stored catalog under
          `pack/.opencode/playbooks/`.
        </Text>
      </Stack>

      <Callout tone="warning" title="Name collision">
        The label is Playbooks. The body is generated suggested prompts from
        `generate_prompts()`. Save writes
        `.opencode/state/tui/suggested-prompts.md`. Stored Playbooks
        (`eha-sib-acceptance`, `repository-deep-review`, …) do not appear.
      </Callout>

      <Row gap={8} align="center">
        <Button
          variant={view === "home" ? "primary" : "secondary"}
          onClick={() => setView("home")}
        >
          Home · button
        </Button>
        <Button
          variant={view === "modal" ? "primary" : "secondary"}
          onClick={() => setView("modal")}
        >
          Modal · CodeSleuth Playbooks
        </Button>
      </Row>

      {view === "home" ? <HomeActions /> : <PlaybooksModal />}

      <H2>Widget tree of the modal</H2>
      <Table
        headers={["Widget", "id", "Region at 120×35"]}
        rows={[
          ["Vertical", "prompt-dialog", "5,2  110×30"],
          ["Horizontal", "page-chrome", "8,4  104×3"],
          ["Button", "abort", "8,4  8×3  · Close"],
          ["Label", "prompt-title", "16,4  96×1  · CodeSleuth Playbooks"],
          ["Static", "(hint)", "8,7  104×2"],
          ["RichLog", "prompt-log", "8,9  104×17"],
          ["Button", "save-prompts", "80,27  16×3  · Save playbooks"],
          ["Button", "close-prompts", "96,27  16×3  · Close"],
        ]}
      />

      <Text size="small" tone="tertiary">
        Source: Textual `export_screenshot` of `CodeSleuthPlaybookScreen` ·
        Home `#playbooks` at Region(x=58, y=9, width=17, height=3) ·
        `pack/.opencode/bin/codesleuth_tui.py`
      </Text>
    </Stack>
  );
}

function HomeActions() {
  return (
    <Stack gap={12}>
      <H2>Home action grid</H2>
      <Text tone="secondary">
        Surface `home` shows `configure`, `smoke` (Verify), `playbooks`,
        `help`, `launch`. Shortcut `p` calls the same `action_playbooks()`.
      </Text>
      <Card>
        <CardHeader trailing={<Pill active>home</Pill>}>
          Home · Evidence Console
        </CardHeader>
        <CardBody>
          <Grid columns={5} gap={8}>
            <ActionCell label="Configure" />
            <ActionCell label="Verify" />
            <ActionCell label="Playbooks" highlight />
            <ActionCell label="Help" />
            <ActionCell label="Open CodeSleuth" />
          </Grid>
          <Text size="small" tone="tertiary" style={{ marginTop: 12 }}>
            `#playbooks` · label Playbooks · visible · 17×3 at column 3 of
            `#actions`
          </Text>
        </CardBody>
      </Card>
    </Stack>
  );
}

function ActionCell({
  label,
  highlight = false,
}: {
  label: string;
  highlight?: boolean;
}) {
  const theme = useHostTheme();
  return (
    <div
      style={{
        padding: "10px 8px",
        textAlign: "center",
        border: `1px solid ${highlight ? theme.accent.primary : theme.stroke.tertiary}`,
        background: highlight ? theme.fill.tertiary : theme.bg.elevated,
        color: highlight ? theme.accent.primary : theme.text.primary,
        fontWeight: highlight ? 600 : 400,
        fontSize: 13,
      }}
    >
      {label}
    </div>
  );
}

function PlaybooksModal() {
  const theme = useHostTheme();
  return (
    <Stack gap={12}>
      <H2>Opened screen</H2>
      <Card>
        <CardHeader trailing={<Pill>CodeSleuthPlaybookScreen</Pill>}>
          CodeSleuth Playbooks
        </CardHeader>
        <CardBody>
          <Row justify="space-between" align="center">
            <Button variant="ghost">Close</Button>
            <Text weight="semibold">CodeSleuth Playbooks</Text>
          </Row>
          <Divider />
          <Text tone="secondary" size="small">
            Ready-to-run review task recipes generated from active repository
            profiles. Playbooks are prompts, not OpenCode Skills; OpenCode
            executes the selected recipe.
          </Text>
          <div
            style={{
              marginTop: 12,
              padding: 12,
              border: `1px solid ${theme.stroke.tertiary}`,
              background: theme.bg.editor,
              maxHeight: 320,
              overflow: "auto",
            }}
          >
            <Stack gap={14}>
              {RECIPES.map((recipe) => (
                <div key={recipe.title}>
                  <Stack gap={4}>
                    <Text weight="semibold">{recipe.title}</Text>
                    <Text size="small" tone="secondary">
                      {recipe.body}
                    </Text>
                  </Stack>
                </div>
              ))}
            </Stack>
          </div>
          <Row justify="end" gap={8} style={{ marginTop: 12 }}>
            <Button variant="primary">Save playbooks</Button>
            <Button variant="secondary">Close</Button>
          </Row>
        </CardBody>
      </Card>
    </Stack>
  );
}
