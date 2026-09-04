use serde_json::{Value, json};
use std::io::Write;
use std::process::{Command, Stdio};

fn bin() -> Command {
    Command::new(env!("CARGO_BIN_EXE_ebca-graph-readside"))
}

fn graph() -> Value {
    json!({
        "graphId": "graph-v1",
        "nodes": [
            {
                "id": "sha256:aaaaaaaa",
                "kind": "file",
                "key": "app",
                "label": "Application",
                "origin": "verified_source"
            },
            {
                "id": "n-helper",
                "kind": "symbol",
                "key": "helper",
                "label": "Helper",
                "origin": "verified_source"
            },
            {
                "id": "n-users",
                "kind": "table",
                "key": "users",
                "label": "Users",
                "origin": "verified_source"
            }
        ],
        "edges": [
            {
                "id": "e-call",
                "relation": "calls",
                "source": "sha256:aaaaaaaa",
                "target": "n-helper",
                "origin": "verified_source"
            },
            {
                "id": "e-read",
                "relation": "reads_from",
                "source": "n-helper",
                "target": "n-users",
                "origin": "verified_source"
            }
        ]
    })
}

fn run_json(request: &Value) -> (i32, Value) {
    let mut child = bin()
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn graph reader");
    child
        .stdin
        .as_mut()
        .expect("stdin")
        .write_all(request.to_string().as_bytes())
        .expect("write request");
    let output = child.wait_with_output().expect("wait for graph reader");
    let stdout = String::from_utf8(output.stdout).expect("utf8 stdout");
    let stderr = String::from_utf8(output.stderr).expect("utf8 stderr");
    assert!(
        stdout
            .lines()
            .all(|line| line.trim().starts_with('{') || line.trim().is_empty()),
        "stdout must be JSON only, got {stdout:?}, stderr {stderr:?}"
    );
    let payload: Value = serde_json::from_str(stdout.trim()).expect("json stdout");
    (output.status.code().unwrap_or(1), payload)
}

#[test]
fn describe_roundtrip_is_machine_json() {
    let (code, payload) = run_json(&json!({
        "operation": "describe",
        "graph": graph(),
    }));
    assert_eq!(code, 0);
    assert_eq!(payload["ok"], true);
    assert_eq!(payload["operation"], "describe");
    assert_eq!(payload["result"]["graphId"], "graph-v1");
    assert_eq!(payload["result"]["nodeCount"], 3);
    assert_eq!(payload["result"]["edgeCount"], 2);
}

#[test]
fn unknown_operation_fails_closed() {
    let (code, payload) = run_json(&json!({
        "operation": "all_paths",
        "graph": graph(),
    }));
    assert_ne!(code, 0);
    assert_eq!(payload["ok"], false);
    assert_eq!(payload["error"]["kind"], "invalid_request");
    assert!(
        payload["error"]["message"]
            .as_str()
            .unwrap()
            .contains("invalid request JSON")
    );
}

#[test]
fn malformed_json_fails_closed() {
    let mut child = bin()
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn graph reader");
    child
        .stdin
        .as_mut()
        .expect("stdin")
        .write_all(b"{not-json")
        .expect("write");
    let output = child.wait_with_output().expect("wait");
    let payload: Value = serde_json::from_slice(&output.stdout)
        .expect("malformed JSON still yields JSON error envelope");
    assert_ne!(output.status.code().unwrap_or(1), 0);
    assert_eq!(payload["ok"], false);
    assert_eq!(payload["error"]["kind"], "invalid_request");
}

#[test]
fn neighbors_cursor_from_other_graph_fails_closed() {
    let first = run_json(&json!({
        "operation": "neighbors",
        "graph": graph(),
        "options": {
            "roots": ["sha256:aaaaaaaa"],
            "direction": "out",
            "hops": 2,
            "nodeLimit": 2,
            "edgeLimit": 1
        }
    }));
    assert_eq!(first.0, 0);
    let cursor = first.1["result"]["nextCursor"].as_str().expect("cursor");
    let mut other = graph();
    other["graphId"] = json!("graph-v2");
    let (code, payload) = run_json(&json!({
        "operation": "neighbors",
        "graph": other,
        "options": {
            "roots": ["sha256:aaaaaaaa"],
            "direction": "out",
            "hops": 2,
            "nodeLimit": 2,
            "edgeLimit": 1,
            "cursor": cursor
        }
    }));
    assert_ne!(code, 0);
    assert_eq!(payload["ok"], false);
    assert_eq!(payload["error"]["kind"], "cursor_mismatch");
}

#[test]
fn version_is_json_not_prose() {
    let output = bin().arg("--version").output().expect("version");
    let payload: Value = serde_json::from_slice(&output.stdout).expect("json version");
    assert!(output.status.success());
    assert_eq!(payload["ok"], true);
    assert_eq!(payload["result"]["name"], "ebca-graph-readside");
}
