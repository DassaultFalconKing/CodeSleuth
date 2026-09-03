use std::collections::BTreeMap;

use ebca_graph_readside::{
    describe, diff, explain, neighbors, resolve, shortest_paths, DiffOptions, Direction, Edge, Graph,
    NeighborOptions, Node, ResolveOptions, ShortestPathOptions,
};
use serde_json::json;

fn node(id: &str, kind: &str, key: &str, label: &str, origin: &str) -> Node {
    Node {
        id: id.into(),
        kind: kind.into(),
        key: key.into(),
        label: Some(label.into()),
        origin: Some(origin.into()),
        source_ref: Some(json!({"path": format!("src/{key}.rs")})),
        metadata: BTreeMap::new(),
    }
}

fn edge(id: &str, relation: &str, source: &str, target: &str, origin: &str) -> Edge {
    Edge {
        id: id.into(),
        relation: relation.into(),
        source: source.into(),
        target: target.into(),
        origin: Some(origin.into()),
        source_ref: None,
        metadata: BTreeMap::new(),
    }
}

fn graph_v1() -> Graph {
    Graph {
        graph_id: "graph-v1".into(),
        nodes: vec![
            node("sha256:aaaaaaaa", "file", "app", "Application", "verified_source"),
            node("n-helper", "symbol", "helper", "Helper", "verified_source"),
            node("n-users", "table", "users", "Users", "verified_source"),
            node("n-api", "external", "payments", "Payments API", "review_inference"),
        ],
        edges: vec![
            edge("e-call", "calls", "sha256:aaaaaaaa", "n-helper", "verified_source"),
            edge("e-read", "reads_from", "n-helper", "n-users", "verified_source"),
            edge("e-api", "depends_on", "sha256:aaaaaaaa", "n-api", "review_inference"),
        ],
        metadata: BTreeMap::new(),
    }
}

#[test]
fn describe_counts_generic_kinds_relations_and_origins() {
    let result = describe(&graph_v1()).expect("valid graph");
    assert_eq!(result.graph_id, "graph-v1");
    assert_eq!(result.node_count, 4);
    assert_eq!(result.edge_count, 3);
    assert_eq!(result.node_kinds["file"], 1);
    assert_eq!(result.node_kinds["symbol"], 1);
    assert_eq!(result.edge_relations["calls"], 1);
    assert_eq!(result.origins["verified_source"], 5);
    assert_eq!(result.origins["review_inference"], 2);
}

#[test]
fn resolve_never_fuzzy_matches_opaque_node_ids() {
    let graph = graph_v1();

    let partial = resolve(
        &graph,
        ResolveOptions {
            query: "aaaaaaaa".into(),
            kinds: vec![],
            origins: vec![],
            limit: 10,
        },
    )
    .expect("valid resolve");
    assert!(partial.matches.is_empty(), "opaque IDs must not participate in fuzzy matching");

    let exact = resolve(
        &graph,
        ResolveOptions {
            query: "sha256:aaaaaaaa".into(),
            kinds: vec![],
            origins: vec![],
            limit: 10,
        },
    )
    .expect("valid resolve");
    assert_eq!(exact.matches.len(), 1);
    assert_eq!(exact.matches[0].node.id, "sha256:aaaaaaaa");
    assert_eq!(exact.matches[0].match_kind, "exact_id");

    let semantic = resolve(
        &graph,
        ResolveOptions {
            query: "help".into(),
            kinds: vec!["symbol".into()],
            origins: vec![],
            limit: 10,
        },
    )
    .expect("valid resolve");
    assert_eq!(semantic.matches[0].node.id, "n-helper");
    assert_eq!(semantic.matches[0].match_kind, "key_prefix");
}

#[test]
fn neighbors_are_bounded_cursor_bound_to_graph_and_never_return_dangling_edges() {
    let graph = graph_v1();
    let first = neighbors(
        &graph,
        NeighborOptions {
            roots: vec!["sha256:aaaaaaaa".into()],
            direction: Direction::Out,
            relations: vec![],
            origins: vec![],
            hops: 2,
            node_limit: 2,
            edge_limit: 1,
            cursor: None,
        },
    )
    .expect("bounded neighborhood");

    assert!(first.nodes.len() <= 2);
    assert!(first.edges.len() <= 1);
    for edge in &first.edges {
        assert!(first.nodes.iter().any(|node| node.id == edge.source));
        assert!(first.nodes.iter().any(|node| node.id == edge.target));
    }
    assert!(first.truncated);
    let cursor = first.next_cursor.clone().expect("continuation cursor");

    let second = neighbors(
        &graph,
        NeighborOptions {
            roots: vec!["sha256:aaaaaaaa".into()],
            direction: Direction::Out,
            relations: vec![],
            origins: vec![],
            hops: 2,
            node_limit: 2,
            edge_limit: 1,
            cursor: Some(cursor.clone()),
        },
    )
    .expect("second page");
    for edge in &second.edges {
        assert!(second.nodes.iter().any(|node| node.id == edge.source));
        assert!(second.nodes.iter().any(|node| node.id == edge.target));
    }

    let mut other = graph.clone();
    other.graph_id = "graph-v2".into();
    let error = neighbors(
        &other,
        NeighborOptions {
            roots: vec!["sha256:aaaaaaaa".into()],
            direction: Direction::Out,
            relations: vec![],
            origins: vec![],
            hops: 2,
            node_limit: 2,
            edge_limit: 1,
            cursor: Some(cursor),
        },
    )
    .expect_err("cursor must be graph-bound");
    assert!(error.to_string().contains("cursor"));
}

#[test]
fn shortest_paths_respect_hop_and_path_bounds() {
    let graph = graph_v1();
    let found = shortest_paths(
        &graph,
        ShortestPathOptions {
            source: "sha256:aaaaaaaa".into(),
            target: "n-users".into(),
            direction: Direction::Out,
            relations: vec![],
            origins: vec![],
            max_hops: 3,
            max_paths: 3,
            expansion_limit: 100,
        },
    )
    .expect("bounded paths");
    assert_eq!(found.paths.len(), 1);
    assert_eq!(found.paths[0].node_ids, vec!["sha256:aaaaaaaa", "n-helper", "n-users"]);
    assert_eq!(found.paths[0].edge_ids, vec!["e-call", "e-read"]);

    let blocked = shortest_paths(
        &graph,
        ShortestPathOptions {
            source: "sha256:aaaaaaaa".into(),
            target: "n-users".into(),
            direction: Direction::Out,
            relations: vec![],
            origins: vec![],
            max_hops: 1,
            max_paths: 3,
            expansion_limit: 100,
        },
    )
    .expect("bounded paths");
    assert!(blocked.paths.is_empty());
}

#[test]
fn explain_returns_exact_element_and_edge_endpoints() {
    let graph = graph_v1();
    let explanation = explain(&graph, "e-read", 10).expect("edge explanation");
    assert_eq!(explanation.element_type, "edge");
    assert_eq!(explanation.edge.as_ref().unwrap().id, "e-read");
    assert_eq!(explanation.source.as_ref().unwrap().id, "n-helper");
    assert_eq!(explanation.target.as_ref().unwrap().id, "n-users");
}

#[test]
fn diff_is_id_based_deterministic_and_bounded() {
    let before = graph_v1();
    let mut after = graph_v1();
    after.graph_id = "graph-v2".into();
    after.nodes[1].label = Some("Helper v2".into());
    after.nodes.push(node("n-audit", "table", "audit", "Audit", "verified_source"));
    after.edges.retain(|edge| edge.id != "e-api");
    after.edges.push(edge("e-audit", "writes_to", "n-helper", "n-audit", "verified_source"));

    let result = diff(&before, &after, DiffOptions { limit: 20 }).expect("graph diff");
    assert_eq!(result.before_graph_id, "graph-v1");
    assert_eq!(result.after_graph_id, "graph-v2");
    assert_eq!(result.added_nodes[0].id, "n-audit");
    assert_eq!(result.changed_nodes[0].before.id, "n-helper");
    assert_eq!(result.removed_edges[0].id, "e-api");
    assert_eq!(result.added_edges[0].id, "e-audit");
    assert!(!result.truncated);
}

#[test]
fn malformed_graphs_fail_closed() {
    let mut duplicate = graph_v1();
    duplicate.nodes.push(duplicate.nodes[0].clone());
    assert!(describe(&duplicate).is_err());

    let mut dangling = graph_v1();
    dangling.edges.push(edge("e-bad", "calls", "missing", "n-helper", "verified_source"));
    assert!(describe(&dangling).is_err());
}
