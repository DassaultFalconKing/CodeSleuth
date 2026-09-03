use ebca_graph_readside::{
    describe, diff, explain, neighbors, resolve, shortest_paths, watermark, DiffOptions, Graph,
    NeighborOptions, ResolveOptions, ShortestPathOptions,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::io::{self, Read};
use std::process::ExitCode;

const MAX_INPUT_BYTES: usize = 32 * 1024 * 1024;

#[derive(Debug, Deserialize)]
#[serde(tag = "operation", rename_all = "snake_case")]
enum Request {
    Describe {
        graph: Graph,
    },
    Resolve {
        graph: Graph,
        options: ResolveOptions,
    },
    Neighbors {
        graph: Graph,
        options: NeighborOptions,
    },
    ShortestPaths {
        graph: Graph,
        options: ShortestPathOptions,
    },
    Explain {
        graph: Graph,
        #[serde(rename = "elementId")]
        element_id: String,
        #[serde(rename = "incidentLimit")]
        incident_limit: usize,
    },
    Diff {
        before: Graph,
        after: Graph,
        options: DiffOptions,
    },
    WatermarkCommit {
        domain: String,
        actor: String,
        #[serde(rename = "parentSha")]
        parent_sha: String,
        subject: String,
    },
    WatermarkSession {
        domain: String,
        actor: String,
        #[serde(rename = "headSha")]
        head_sha: String,
        #[serde(rename = "sessionId")]
        session_id: String,
    },
}

fn to_value<T: serde::Serialize>(value: T) -> Result<Value, String> {
    serde_json::to_value(value).map_err(|error| format!("cannot serialize result: {error}"))
}

fn dispatch(request: Request) -> Result<(&'static str, Value), String> {
    match request {
        Request::Describe { graph } => describe(&graph)
            .map_err(|error| error.to_string())
            .and_then(|result| to_value(result).map(|value| ("describe", value))),
        Request::Resolve { graph, options } => resolve(&graph, options)
            .map_err(|error| error.to_string())
            .and_then(|result| to_value(result).map(|value| ("resolve", value))),
        Request::Neighbors { graph, options } => neighbors(&graph, options)
            .map_err(|error| error.to_string())
            .and_then(|result| to_value(result).map(|value| ("neighbors", value))),
        Request::ShortestPaths { graph, options } => shortest_paths(&graph, options)
            .map_err(|error| error.to_string())
            .and_then(|result| to_value(result).map(|value| ("shortest_paths", value))),
        Request::Explain {
            graph,
            element_id,
            incident_limit,
        } => explain(&graph, &element_id, incident_limit)
            .map_err(|error| error.to_string())
            .and_then(|result| to_value(result).map(|value| ("explain", value))),
        Request::Diff {
            before,
            after,
            options,
        } => diff(&before, &after, options)
            .map_err(|error| error.to_string())
            .and_then(|result| to_value(result).map(|value| ("diff", value))),
        Request::WatermarkCommit {
            domain,
            actor,
            parent_sha,
            subject,
        } => watermark::commit_watermark(&domain, &actor, &parent_sha, &subject)
            .map_err(|error| error.to_string())
            .map(|result| ("watermark_commit", json!({ "watermark": result }))),
        Request::WatermarkSession {
            domain,
            actor,
            head_sha,
            session_id,
        } => watermark::session_watermark(&domain, &actor, &head_sha, &session_id)
            .map_err(|error| error.to_string())
            .map(|result| ("watermark_session", json!({ "watermark": result }))),
    }
}

fn print_error(message: impl AsRef<str>) -> ExitCode {
    let payload = json!({
        "schemaVersion": 1,
        "ok": false,
        "error": { "message": message.as_ref() },
    });
    println!("{}", payload);
    ExitCode::from(2)
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args == ["--version"] {
        println!("ebca-graph-readside {}", env!("CARGO_PKG_VERSION"));
        return ExitCode::SUCCESS;
    }
    if !args.is_empty() {
        return print_error("ebca-graph-readside accepts only --version or one JSON request on stdin");
    }

    let mut input = Vec::new();
    let mut stdin = io::stdin().take((MAX_INPUT_BYTES + 1) as u64);
    if let Err(error) = stdin.read_to_end(&mut input) {
        return print_error(format!("cannot read request: {error}"));
    }
    if input.len() > MAX_INPUT_BYTES {
        return print_error(format!("request exceeds {MAX_INPUT_BYTES} byte hard bound"));
    }

    let request: Request = match serde_json::from_slice(&input) {
        Ok(request) => request,
        Err(error) => return print_error(format!("invalid request JSON: {error}")),
    };

    match dispatch(request) {
        Ok((operation, result)) => {
            println!(
                "{}",
                json!({
                    "schemaVersion": 1,
                    "ok": true,
                    "operation": operation,
                    "result": result,
                })
            );
            ExitCode::SUCCESS
        }
        Err(error) => print_error(error),
    }
}
