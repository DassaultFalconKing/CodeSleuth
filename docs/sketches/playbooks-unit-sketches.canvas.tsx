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
  H3,
  Pill,
  Row,
  Stack,
  Table,
  Text,
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

type View = "map" | "catalog" | "detail" | "wizard";

const PLAYBOOKS = [
  {
    id: "repository-deep-review",
    steps: 5,
    command: "/repo-review",
    origin: "pack",
    description: "Evidence-first whole-repository or PR review.",
  },
  {
    id: "repository-map",
    steps: 2,
    command: "/repo-map",
    origin: "pack",
    description: "Bounded context projection + optional Mermaid.",
  },
  {
    id: "repository-documentation",
    steps: 4,
    command: "/repo-docs",
    origin: "pack",
    description: "Docs from verified implementation/config/test evidence.",
  },
  {
    id: "protected-capability-assessment",
    steps: 5,
    command: "/repo-contracts",
    origin: "pack",
    description: "Registry + forbidden-regression impact for a query/diff.",
  },
  {
    id: "feature-port",
    steps: 6,
    command: "/repo-port",
    origin: "pack",
    description: "Semantic port from exact source to target-native delta.",
  },
  {
    id: "eha-sib-acceptance",
    steps: 6,
    command: "/eha-test",
    origin: "pack",
    description: "SIB0/SIB1/SIB2 Exact-Head Acceptance on one SHA.",
  },
  {
    id: "eha-repair",
    steps: 3,
    command: "/eha-repair",
    origin: "pack",
    description: "Repair one recorded EHA blocker; do not rewrite FAIL.",
  },
] as const;

const EHA_STEPS = [
  {
    n: 1,
    id: "select-candidate",
    kind: "step",
    skills: ["exact-target-identity", "eha-candidate-selection"],
    tools: [] as string[],
    output: "candidate_identity",
    isolation: "fresh_subagent",
    note: "Заморозить literal HEAD release-stream. Не подменять PR/repair SHA.",
  },
  {
    n: 2,
    id: "start-campaign",
    kind: "step",
    skills: ["eha-campaign-evidence"],
    tools: ["review_state", "eha_state_start_campaign"],
    output: "campaign_started",
    isolation: "fresh_subagent",
    note: "Старт durable campaign на том же SHA.",
  },
  {
    n: 3,
    id: "sib0-profile",
    kind: "step",
    skills: ["eha-campaign-evidence", "protected-capability-registry"],
    tools: ["review_state_record_finding", "eha_state_record_verdict"],
    output: "sib0_verdict",
    isolation: "fresh_subagent",
    note: "Только архитектурный профиль. FAIL замораживает SHA.",
  },
  {
    n: 4,
    id: "sib1-profile",
    kind: "step",
    skills: ["eha-campaign-evidence", "contract-triangulation"],
    tools: ["review_state_record_finding", "eha_state_record_verdict"],
    output: "sib1_verdict",
    isolation: "fresh_subagent",
    note: "SIB1 claimable только если SIB0 PASS на том же SHA.",
  },
  {
    n: 5,
    id: "sib2-profile",
    kind: "step",
    skills: ["eha-campaign-evidence", "acceptance-matrix-design"],
    tools: ["review_state_record_finding", "eha_state_record_verdict"],
    output: "sib2_verdict",
    isolation: "fresh_subagent",
    note: "Полный canonical profile, включая TUI visual regression.",
  },
  {
    n: 6,
    id: "persist-report",
    kind: "skill",
    skills: ["codesleuth-reports"],
    tools: [] as string[],
    output: "report_path",
    isolation: "fresh_subagent",
    note: "Отчёт — производный view. Ledger остаётся authority.",
  },
] as const;

const WIZARD = [
  {
    id: 1,
    title: "Source",
    body: "Папка playbooks/{id}/ или zip с PLAYBOOK.md + playbook.json + steps/.",
  },
  {
    id: 2,
    title: "Inspect",
    body: "id, description, step count, referenced skills/tools, origin path.",
  },
  {
    id: 3,
    title: "Validate",
    body: "schema, id==folder, DAG ацикличен, skills существуют или warning.",
  },
  {
    id: 4,
    title: "Confirm",
    body: "Куда ставим (.opencode/playbooks overlay). Collision с pack — не silent overwrite.",
  },
  {
    id: 5,
    title: "Result",
    body: "Появился в каталоге. TUI не запускает шаги. Дальше /playbook {id}.",
  },
] as const;

export default function PlaybooksUnitSketches() {
  const [view, setView] = useCanvasState<View>("sketch-view", "map");
  const [wizardStep, setWizardStep] = useCanvasState<number>("wizard-step", 1);

  return (
    <Stack gap={20}>
      <Stack gap={8}>
        <H1>Эскизы нового юнита Playbooks</H1>
        <Text tone="secondary">
          Не реализация. Замена текущей модалки `CodeSleuthPlaybookScreen`
          (RichLog с `/repo-*` промптами) на каталог stored Playbooks +
          детальный разбор шага + мастер загрузки. Исполнение остаётся у
          OpenCode `build` через `/playbook`.
        </Text>
      </Stack>

      <Row gap={8} wrap>
        <Button
          variant={view === "map" ? "primary" : "secondary"}
          onClick={() => setView("map")}
        >
          0. Карта юнита
        </Button>
        <Button
          variant={view === "catalog" ? "primary" : "secondary"}
          onClick={() => setView("catalog")}
        >
          1. Каталог
        </Button>
        <Button
          variant={view === "detail" ? "primary" : "secondary"}
          onClick={() => setView("detail")}
        >
          2. Карточка плейбука
        </Button>
        <Button
          variant={view === "wizard" ? "primary" : "secondary"}
          onClick={() => setView("wizard")}
        >
          3. Мастер загрузки
        </Button>
      </Row>

      {view === "map" ? <MapSketch onOpenCatalog={() => setView("catalog")} /> : null}
      {view === "catalog" ? (
        <CatalogSketch
          onOpenDetail={() => setView("detail")}
          onOpenWizard={() => setView("wizard")}
        />
      ) : null}
      {view === "detail" ? (
        <DetailSketch onBack={() => setView("catalog")} />
      ) : null}
      {view === "wizard" ? (
        <WizardSketch
          step={wizardStep}
          setStep={setWizardStep}
          onDone={() => setView("catalog")}
        />
      ) : null}
    </Stack>
  );
}

function MapSketch({ onOpenCatalog }: { onOpenCatalog: () => void }) {
  return (
    <Grid columns="1.4fr 1fr" gap={20}>
      <Stack gap={12}>
        <H2>Куда садится юнит</H2>
        <TuiChrome highlight="playbooks" />
        <Card>
          <CardHeader>Home / Review больше не открывают лог промптов</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Кнопка `Playbooks` и хоткей `p` ведут на эту поверхность, не
                на `generate_prompts()`.
              </Text>
              <Text>
                Старый список `/repo-review` recipes уезжает в Review как
                **Suggested prompts** (или остаётся `/repo-prompts` в хосте).
                Имя не должно совпадать.
              </Text>
              <Button variant="primary" onClick={onOpenCatalog}>
                Открыть эскиз каталога
              </Button>
            </Stack>
          </CardBody>
        </Card>
      </Stack>
      <Stack gap={12}>
        <H2>Комментарии</H2>
        <Callout tone="info" title="C1 · отдельное меню">
          Новый nav-route `playbooks`, не модалка поверх Home. Оператор
          должен попасть сюда так же, как в Evidence/Tools.
        </Callout>
        <Callout tone="warning" title="C2 · не второй раннер">
          TUI только показывает манифест и ставит файлы. Запуск =
          скопировать `/playbook eha-sib-acceptance` или Open CodeSleuth.
          Шаги по-прежнему один за раз, host-native subagent.
        </Callout>
        <Callout title="C3 · слой SIB">
          Feature population внутри `CC-TUI` + `CC-PACK`. Каталог и
          install UX уже разрешены product contract §5–6.
        </Callout>
      </Stack>
    </Grid>
  );
}

function CatalogSketch({
  onOpenDetail,
  onOpenWizard,
}: {
  onOpenDetail: () => void;
  onOpenWizard: () => void;
}) {
  return (
    <Grid columns="1.5fr 1fr" gap={20}>
      <Stack gap={12}>
        <H2>1. Каталог — кликабельные строки</H2>
        <Card>
          <CardHeader trailing={<Pill tone="info">pack + overlay</Pill>}>
            Playbooks · installed catalog
          </CardHeader>
          <CardBody>
            <Row justify="space-between" align="center">
              <Text weight="semibold">7 installed</Text>
              <Row gap={8}>
                <Button variant="primary" onClick={onOpenWizard}>
                  Load playbook
                </Button>
                <Button variant="secondary">Copy /playbook</Button>
              </Row>
            </Row>
            <Divider />
            <Table
              headers={["Playbook", "Steps", "Command", "Origin"]}
              rows={PLAYBOOKS.map((item) => [
                item.id === "eha-sib-acceptance" ? (
                  <Button variant="ghost" onClick={onOpenDetail}>
                    {item.id}
                  </Button>
                ) : (
                  item.id
                ),
                String(item.steps),
                item.command,
                item.origin,
              ])}
            />
            <Text size="small" tone="tertiary">
              Эскиз: клик по `eha-sib-acceptance` открывает карточку. Остальные
              строки в TUI тоже кнопки; здесь для примера одна.
            </Text>
          </CardBody>
        </Card>
      </Stack>
      <Stack gap={12}>
        <H2>Комментарии</H2>
        <Callout tone="info" title="C4 · строка = объект">
          Не RichLog. Каждая строка — отдельный control. Enter/клик →
          detail. Сейчас на скрине 1/2/3 — мёртвый текст.
        </Callout>
        <Callout title="C5 · источник правды">
          Список из overlay `.opencode/playbooks/*/playbook.json`, затем
          pack. Не из `generate_prompts()`.
        </Callout>
        <Callout tone="warning" title="C6 · Save playbooks убрать">
          Кнопка Save писала `suggested-prompts.md`. В новом юните её нет.
          Загрузка — только мастер, с validate.
        </Callout>
        <Callout title="C7 · Launch не execute">
          Copy `/playbook {'{id}'}` или Open CodeSleuth. TUI не materialize Step.
        </Callout>
      </Stack>
    </Grid>
  );
}

function DetailSketch({ onBack }: { onBack: () => void }) {
  return (
    <Grid columns="1.6fr 1fr" gap={20}>
      <Stack gap={12}>
        <H2>2. Карточка плейбука — шаги, skills, tools</H2>
        <Card>
          <CardHeader trailing={<Pill active>eha-sib-acceptance</Pill>}>
            Exact-Head Acceptance
          </CardHeader>
          <CardBody>
            <Row justify="space-between" align="center">
              <Button variant="ghost" onClick={onBack}>
                Back to catalog
              </Button>
              <Row gap={8}>
                <Pill tone="info">pack</Pill>
                <Pill>6 steps</Pill>
                <Pill>/eha-test</Pill>
              </Row>
            </Row>
            <Text tone="secondary">
              Exact-Head Acceptance campaign for SIB0, SIB1, and SIB2 on one
              immutable release-stream SHA.
            </Text>
            <Row gap={8} justify="end">
              <Button variant="secondary">Copy /playbook eha-sib-acceptance</Button>
              <Button variant="primary">Open in OpenCode</Button>
            </Row>
            <Divider />
            <H3>Steps · модель применяет только объявленное на шаге</H3>
            <Stack gap={10}>
              {EHA_STEPS.map((step) => (
                <div key={step.id}>
                  <StepRow step={step} />
                </div>
              ))}
            </Stack>
          </CardBody>
        </Card>
      </Stack>
      <Stack gap={12}>
        <H2>Комментарии</H2>
        <Callout tone="info" title="C8 · хайлайты, не запуск">
          Чип Skill / Tool — карточка контракта (Input/Objective/Stop).
          Клик не вызывает tool и не грузит Skill в модель из TUI.
        </Callout>
        <Callout title="C9 · tools[] в манифесте">
          Сейчас tools только в markdown шага. Для стабильных хайлайтов —
          optional `tools[]` на step в `playbook.json`. Эскиз уже показывает
          целевой вид.
        </Callout>
        <Callout tone="warning" title="C10 · один шаг за раз">
          Карточка показывает весь DAG для оператора. Хост по-прежнему
          materialize ровно один Step и грузит только его Skills.
        </Callout>
        <Callout title="C11 · kind">
          `execution=skill` (шаг 6) vs `execution=step`. Не плодить
          фейковый Skill, если инструкция живёт только в этом плейбуке.
        </Callout>
        <Callout title="C12 · isolation">
          Почти везде `fresh_subagent`. Если хост не умеет — не врать;
          `STEP_ISOLATION_UNPROVEN`.
        </Callout>
      </Stack>
    </Grid>
  );
}

function StepRow({
  step,
}: {
  step: (typeof EHA_STEPS)[number];
}) {
  const theme = useHostTheme();
  return (
    <div
      style={{
        padding: 10,
        border: `1px solid ${theme.stroke.tertiary}`,
        background: theme.bg.editor,
      }}
    >
      <Row align="center" gap={8}>
        <Text weight="semibold">
          {step.n}. {step.id}
        </Text>
        <Pill size="sm" tone={step.kind === "skill" ? "renamed" : "neutral"}>
          {step.kind}
        </Pill>
        <Pill size="sm">{step.isolation}</Pill>
        <Text size="small" tone="tertiary">
          → {step.output}
        </Text>
      </Row>
      <Text size="small" tone="secondary">
        {step.note}
      </Text>
      <Row gap={6} wrap>
        {step.skills.map((skill) => (
          <span key={skill}>
            <Pill size="sm" tone="info" active>
              skill:{skill}
            </Pill>
          </span>
        ))}
        {step.tools.map((tool) => (
          <span key={tool}>
            <Pill size="sm" tone="warning">
              tool:{tool}
            </Pill>
          </span>
        ))}
        {step.tools.length === 0 ? (
          <Text size="small" tone="tertiary">
            tools: none declared
          </Text>
        ) : null}
      </Row>
    </div>
  );
}

function WizardSketch({
  step,
  setStep,
  onDone,
}: {
  step: number;
  setStep: (n: number) => void;
  onDone: () => void;
}) {
  const current = WIZARD[step - 1];
  return (
    <Grid columns="1.4fr 1fr" gap={20}>
      <Stack gap={12}>
        <H2>3. Мастер загрузки нового плейбука</H2>
        <Row gap={8} wrap>
          {WIZARD.map((item) => (
            <span key={item.id}>
              <Button
                variant={item.id === step ? "primary" : "secondary"}
                onClick={() => setStep(item.id)}
              >
                {item.id}. {item.title}
              </Button>
            </span>
          ))}
        </Row>
        <Card>
          <CardHeader trailing={<Pill>step {step}/5</Pill>}>
            Load playbook · {current.title}
          </CardHeader>
          <CardBody>
            <WizardBody step={step} />
            <Row justify="space-between" style={{ marginTop: 16 }}>
              <Button
                variant="ghost"
                disabled={step === 1}
                onClick={() => setStep(Math.max(1, step - 1))}
              >
                Back
              </Button>
              {step < 5 ? (
                <Button variant="primary" onClick={() => setStep(step + 1)}>
                  Continue
                </Button>
              ) : (
                <Button variant="primary" onClick={onDone}>
                  Open catalog
                </Button>
              )}
            </Row>
          </CardBody>
        </Card>
      </Stack>
      <Stack gap={12}>
        <H2>Комментарии</H2>
        <Callout tone="info" title="C13 · inspect before write">
          Сначала показать манифест. Копирование файлов — только после
          Validate + Confirm.
        </Callout>
        <Callout tone="warning" title="C14 · те же инварианты, что тесты">
          `id` == имя папки, есть `PLAYBOOK.md`, шаги существуют, DAG без
          циклов, skills реальные или явный warning. Как
          `tests/test_playbook_skill_contract.py`.
        </Callout>
        <Callout title="C15 · overlay, не pack mutate">
          Пользовательский плейбук → target `.opencode/playbooks/{'{id}'}/`.
          Builtin pack не переписываем без confirm conflict.
        </Callout>
        <Callout tone="warning" title="C16 · после install не execute">
          Мастер не стартует `/playbook`. Иначе TUI станет контроллером.
        </Callout>
        <Callout title="C17 · phase 2">
          Remote URL / registry — позже. В первом срезе: локальная папка и
          zip.
        </Callout>
      </Stack>
    </Grid>
  );
}

function WizardBody({ step }: { step: number }) {
  if (step === 1) {
    return (
      <Stack gap={8}>
        <Text>Источник</Text>
        <Text tone="secondary">
          `C:\Users\testc\playbooks\team-security-pass\`
        </Text>
        <Text size="small" tone="tertiary">
          Ожидаемый layout: PLAYBOOK.md, playbook.json, steps/*.md
        </Text>
      </Stack>
    );
  }
  if (step === 2) {
    return (
      <Stack gap={8}>
        <Text weight="semibold">team-security-pass</Text>
        <Text tone="secondary">
          Bounded security-pass over auth/session surfaces.
        </Text>
        <Table
          headers={["Field", "Value"]}
          rows={[
            ["schema_version", "1"],
            ["steps", "4"],
            ["skills", "exact-target-identity, repository-deep-review"],
            ["tools declared", "none → warning on validate"],
          ]}
        />
      </Stack>
    );
  }
  if (step === 3) {
    return (
      <Stack gap={8}>
        <Row gap={8}>
          <Pill tone="success">schema ok</Pill>
          <Pill tone="success">DAG acyclic</Pill>
          <Pill tone="success">PLAYBOOK.md present</Pill>
          <Pill tone="warning">tools[] empty</Pill>
        </Row>
        <Text tone="secondary">
          Skills резолвятся в установленном pack. tools не объявлены —
          каталог покажет `tools: none declared`, не выдумает имена из
          markdown.
        </Text>
      </Stack>
    );
  }
  if (step === 4) {
    return (
      <Stack gap={8}>
        <Text>
          Install to `.opencode/playbooks/team-security-pass/` in the
          selected target repo.
        </Text>
        <Text tone="secondary">
          Collision with pack id: none. Overwrite existing overlay: no.
        </Text>
        <Callout tone="warning" title="Confirm">
          Это запись файлов, не запуск агента. Conflict-safe: не трогаем
          builtin `pack/.opencode/playbooks/`.
        </Callout>
      </Stack>
    );
  }
  return (
    <Stack gap={8}>
      <Pill tone="success">installed</Pill>
      <Text>
        `team-security-pass` теперь в каталоге. Следующее действие
        оператора: `/playbook team-security-pass`.
      </Text>
    </Stack>
  );
}

function TuiChrome({ highlight }: { highlight: string }) {
  const theme = useHostTheme();
  const surfaces = [
    "home",
    "review",
    "evidence",
    "tools",
    "playbooks",
    "settings",
  ];
  return (
    <div
      style={{
        border: `1px solid ${theme.stroke.secondary}`,
        background: theme.bg.editor,
        padding: 12,
      }}
    >
      <Text size="small" tone="tertiary">
        TUI chrome · эскиз nav
      </Text>
      <Row gap={8} style={{ marginTop: 8 }}>
        <Stack gap={6} style={{ width: 120 }}>
          {surfaces.map((name) => (
            <div
              key={name}
              style={{
                padding: "6px 8px",
                background:
                  name === highlight ? theme.fill.tertiary : "transparent",
                border:
                  name === highlight
                    ? `1px solid ${theme.accent.primary}`
                    : `1px solid ${theme.stroke.tertiary}`,
                color:
                  name === highlight
                    ? theme.accent.primary
                    : theme.text.secondary,
                fontSize: 12,
              }}
            >
              {name}
            </div>
          ))}
        </Stack>
        <div
          style={{
            flex: 1,
            padding: 12,
            border: `1px solid ${theme.stroke.tertiary}`,
            minHeight: 180,
          }}
        >
          <Text weight="semibold">Playbooks · catalog</Text>
          <Text size="small" tone="secondary">
            Список установленных плейбуков. Load playbook справа сверху.
            Клик по строке → карточка шагов.
          </Text>
        </div>
      </Row>
    </div>
  );
}
