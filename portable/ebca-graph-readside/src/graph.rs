use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet, VecDeque};
use std::error::Error;
use std::fmt::{Display, Formatter};

const MAX_GRAPH_NODES: usize = 100_000;
const MAX_GRAPH_EDGES: usize = 500_000;
const MAX_RESOLVE_LIMIT: usize = 100;
const MAX_NEIGHBOR_HOPS: u8 = 6;
const MAX_NEIGHBOR_NODE_LIMIT: usize = 500;
const MAX_NEIGHBOR_EDGE_LIMIT: usize = 1_000;
const MAX_NEIGHBOR_SELECTED_NODES: usize = 5_000;
const MAX_NEIGHBOR_SELECTED_EDGES: usize = 20_000;
const MAX_NEIGHBOR_EXPANSIONS: usize = 50_000;
const MAX_PATH_HOPS: u8 = 6;
const MAX_PATHS: usize = 10;
const MAX_PATH_EXPANSIONS: usize = 50_000;
const MAX_EXPLAIN_INCIDENT: usize = 200;
const MAX_DIFF_LIMIT: usize = 500;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReadsideError {
    message: String,
}

impl ReadsideError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

impl Display for ReadsideError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.message)
    }
}

impl Error for ReadsideError {}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Node {
    pub id: String,
    pub kind: String,
    pub key: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub label: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub origin: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_ref: Option<Value>,
    #[serde(default)]
    pub metadata: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Edge {
    pub id: String,
    pub relation: String,
    pub source: String,
    pub target: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub origin: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_ref: Option<Value>,
    #[serde(default)]
    pub metadata: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Graph {
    pub graph_id: String,
    #[serde(default)]
    pub nodes: Vec<Node>,
    #[serde(default)]
    pub edges: Vec<Edge>,
    #[serde(default)]
    pub metadata: BTreeMap<String, Value>,
}

#[derive(Debug)]
struct Validated<'a> {
    nodes: BTreeMap<&'a str, &'a Node>,
    edges: BTreeMap<&'a str, &'a Edge>,
}

fn validate_text(value: &str, what: &str) -> Result<(), ReadsideError> {
    if value.trim().is_empty() {
        return Err(ReadsideError::new(format!("{what} must not be empty")));
    }
    if value.chars().any(char::is_control) {
        return Err(ReadsideError::new(format!("{what} must not contain control characters")));
    }
    Ok(())
}

fn validate_graph(graph: &Graph) -> Result<Validated<'_>, ReadsideError> {
    validate_text(&graph.graph_id, "graph_id")?;
    if graph.nodes.len() > MAX_GRAPH_NODES {
        return Err(ReadsideError::new(format!(
            "graph exceeds {MAX_GRAPH_NODES} node hard bound"
        )));
    }
    if graph.edges.len() > MAX_GRAPH_EDGES {
        return Err(ReadsideError::new(format!(
            "graph exceeds {MAX_GRAPH_EDGES} edge hard bound"
        )));
    }

    let mut nodes = BTreeMap::new();
    let mut all_ids = HashSet::new();
    for node in &graph.nodes {
        validate_text(&node.id, "node id")?;
        validate_text(&node.kind, "node kind")?;
        validate_text(&node.key, "node key")?;
        if !all_ids.insert(node.id.as_str()) {
            return Err(ReadsideError::new(format!("duplicate graph element id: {}", node.id)));
        }
        nodes.insert(node.id.as_str(), node);
    }

    let mut edges = BTreeMap::new();
    for edge in &graph.edges {
        validate_text(&edge.id, "edge id")?;
        validate_text(&edge.relation, "edge relation")?;
        validate_text(&edge.source, "edge source")?;
        validate_text(&edge.target, "edge target")?;
        if !all_ids.insert(edge.id.as_str()) {
            return Err(ReadsideError::new(format!("duplicate graph element id: {}", edge.id)));
        }
        if !nodes.contains_key(edge.source.as_str()) {
            return Err(ReadsideError::new(format!(
                "edge {} references missing source node {}",
                edge.id, edge.source
            )));
        }
        if !nodes.contains_key(edge.target.as_str()) {
            return Err(ReadsideError::new(format!(
                "edge {} references missing target node {}",
                edge.id, edge.target
            )));
        }
        edges.insert(edge.id.as_str(), edge);
    }

    Ok(Validated { nodes, edges })
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct DescribeResult {
    pub graph_id: String,
    pub node_count: usize,
    pub edge_count: usize,
    pub node_kinds: BTreeMap<String, usize>,
    pub edge_relations: BTreeMap<String, usize>,
    pub origins: BTreeMap<String, usize>,
}

pub fn describe(graph: &Graph) -> Result<DescribeResult, ReadsideError> {
    validate_graph(graph)?;
    let mut node_kinds = BTreeMap::new();
    let mut edge_relations = BTreeMap::new();
    let mut origins = BTreeMap::new();

    for node in &graph.nodes {
        *node_kinds.entry(node.kind.clone()).or_insert(0) += 1;
        if let Some(origin) = &node.origin {
            *origins.entry(origin.clone()).or_insert(0) += 1;
        }
    }
    for edge in &graph.edges {
        *edge_relations.entry(edge.relation.clone()).or_insert(0) += 1;
        if let Some(origin) = &edge.origin {
            *origins.entry(origin.clone()).or_insert(0) += 1;
        }
    }

    Ok(DescribeResult {
        graph_id: graph.graph_id.clone(),
        node_count: graph.nodes.len(),
        edge_count: graph.edges.len(),
        node_kinds,
        edge_relations,
        origins,
    })
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct ResolveOptions {
    pub query: String,
    #[serde(default)]
    pub kinds: Vec<String>,
    #[serde(default)]
    pub origins: Vec<String>,
    pub limit: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ResolveMatch {
    pub node: Node,
    pub match_kind: String,
    pub score: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ResolveResult {
    pub matches: Vec<ResolveMatch>,
    pub truncated: bool,
}

fn lower(value: &str) -> String {
    value.to_lowercase()
}

pub fn resolve(graph: &Graph, options: ResolveOptions) -> Result<ResolveResult, ReadsideError> {
    validate_graph(graph)?;
    let query = options.query.trim();
    if query.is_empty() {
        return Err(ReadsideError::new("resolve query must not be empty"));
    }
    if options.limit == 0 || options.limit > MAX_RESOLVE_LIMIT {
        return Err(ReadsideError::new(format!(
            "resolve limit must be 1..{MAX_RESOLVE_LIMIT}"
        )));
    }

    let kinds: BTreeSet<&str> = options.kinds.iter().map(String::as_str).collect();
    let origins: BTreeSet<&str> = options.origins.iter().map(String::as_str).collect();
    let query_lower = lower(query);
    let mut matches = Vec::new();

    for node in &graph.nodes {
        if !kinds.is_empty() && !kinds.contains(node.kind.as_str()) {
            continue;
        }
        if !origins.is_empty()
            && !node
                .origin
                .as_deref()
                .is_some_and(|origin| origins.contains(origin))
        {
            continue;
        }

        let key_lower = lower(&node.key);
        let label_lower = node.label.as_deref().map(lower);
        let matched = if node.id == query {
            Some(("exact_id", 1000))
        } else if key_lower == query_lower {
            Some(("exact_key", 900))
        } else if label_lower.as_deref() == Some(query_lower.as_str()) {
            Some(("exact_label", 800))
        } else if key_lower.starts_with(&query_lower) {
            Some(("key_prefix", 700))
        } else if label_lower
            .as_deref()
            .is_some_and(|label| label.starts_with(&query_lower))
        {
            Some(("label_prefix", 600))
        } else if key_lower.contains(&query_lower) {
            Some(("key_substring", 500))
        } else if label_lower
            .as_deref()
            .is_some_and(|label| label.contains(&query_lower))
        {
            Some(("label_substring", 400))
        } else {
            None
        };

        if let Some((match_kind, score)) = matched {
            matches.push(ResolveMatch {
                node: node.clone(),
                match_kind: match_kind.to_string(),
                score,
            });
        }
    }

    matches.sort_by(|a, b| {
        b.score
            .cmp(&a.score)
            .then_with(|| lower(&a.node.key).cmp(&lower(&b.node.key)))
            .then_with(|| a.node.kind.cmp(&b.node.kind))
            .then_with(|| a.node.id.cmp(&b.node.id))
    });
    let truncated = matches.len() > options.limit;
    matches.truncate(options.limit);
    Ok(ResolveResult { matches, truncated })
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Direction {
    Out,
    In,
    Both,
}

impl Direction {
    fn label(self) -> &'static str {
        match self {
            Self::Out => "out",
            Self::In => "in",
            Self::Both => "both",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct NeighborOptions {
    pub roots: Vec<String>,
    pub direction: Direction,
    #[serde(default)]
    pub relations: Vec<String>,
    #[serde(default)]
    pub origins: Vec<String>,
    pub hops: u8,
    pub node_limit: usize,
    pub edge_limit: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct SelectionTotals {
    pub nodes: usize,
    pub edges: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct NeighborhoodResult {
    pub graph_id: String,
    pub nodes: Vec<Node>,
    pub edges: Vec<Edge>,
    pub totals: SelectionTotals,
    pub truncated: bool,
    pub selection_truncated: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
}

#[derive(Debug)]
struct NeighborhoodSelection {
    node_ids: Vec<String>,
    edge_ids: Vec<String>,
    truncated: bool,
}

fn filter_set(values: &[String]) -> BTreeSet<&str> {
    values.iter().map(String::as_str).collect()
}

fn edge_passes_filters(edge: &Edge, relations: &BTreeSet<&str>, origins: &BTreeSet<&str>) -> bool {
    if !relations.is_empty() && !relations.contains(edge.relation.as_str()) {
        return false;
    }
    if !origins.is_empty()
        && !edge
            .origin
            .as_deref()
            .is_some_and(|origin| origins.contains(origin))
    {
        return false;
    }
    true
}

fn neighbor_for<'a>(edge: &'a Edge, node_id: &str, direction: Direction) -> Option<&'a str> {
    match direction {
        Direction::Out if edge.source == node_id => Some(edge.target.as_str()),
        Direction::In if edge.target == node_id => Some(edge.source.as_str()),
        Direction::Both if edge.source == node_id => Some(edge.target.as_str()),
        Direction::Both if edge.target == node_id => Some(edge.source.as_str()),
        _ => None,
    }
}

fn select_neighborhood(graph: &Graph, options: &NeighborOptions) -> Result<NeighborhoodSelection, ReadsideError> {
    let validated = validate_graph(graph)?;
    if options.roots.is_empty() {
        return Err(ReadsideError::new("neighbors requires at least one exact root node id"));
    }
    if options.roots.len() > 50 {
        return Err(ReadsideError::new("neighbors accepts at most 50 roots"));
    }
    if options.hops > MAX_NEIGHBOR_HOPS {
        return Err(ReadsideError::new(format!(
            "neighbors hops must be 0..{MAX_NEIGHBOR_HOPS}"
        )));
    }

    let relations = filter_set(&options.relations);
    let origins = filter_set(&options.origins);
    let mut adjacency: HashMap<&str, Vec<&Edge>> = HashMap::new();
    for edge in &graph.edges {
        if !edge_passes_filters(edge, &relations, &origins) {
            continue;
        }
        match options.direction {
            Direction::Out => adjacency.entry(edge.source.as_str()).or_default().push(edge),
            Direction::In => adjacency.entry(edge.target.as_str()).or_default().push(edge),
            Direction::Both => {
                adjacency.entry(edge.source.as_str()).or_default().push(edge);
                if edge.target != edge.source {
                    adjacency.entry(edge.target.as_str()).or_default().push(edge);
                }
            }
        }
    }
    for edges in adjacency.values_mut() {
        edges.sort_by(|a, b| a.id.cmp(&b.id));
    }

    let mut roots = options.roots.clone();
    roots.sort();
    roots.dedup();
    for root in &roots {
        if !validated.nodes.contains_key(root.as_str()) {
            return Err(ReadsideError::new(format!("root node does not exist: {root}")));
        }
    }

    let mut visited: HashSet<String> = HashSet::new();
    let mut node_ids = Vec::new();
    let mut queue = VecDeque::new();
    for root in roots {
        visited.insert(root.clone());
        node_ids.push(root.clone());
        queue.push_back((root, 0_u8));
    }

    let mut seen_edges = HashSet::new();
    let mut edge_ids = Vec::new();
    let mut expansions = 0_usize;
    let mut truncated = false;

    'walk: while let Some((node_id, depth)) = queue.pop_front() {
        if depth >= options.hops {
            continue;
        }
        for edge in adjacency.get(node_id.as_str()).into_iter().flatten() {
            if expansions >= MAX_NEIGHBOR_EXPANSIONS {
                truncated = true;
                break 'walk;
            }
            expansions += 1;
            let Some(other) = neighbor_for(edge, &node_id, options.direction) else {
                continue;
            };
            if !visited.contains(other) && visited.len() >= MAX_NEIGHBOR_SELECTED_NODES {
                truncated = true;
                break 'walk;
            }
            if !seen_edges.contains(edge.id.as_str()) && seen_edges.len() >= MAX_NEIGHBOR_SELECTED_EDGES {
                truncated = true;
                break 'walk;
            }
            if seen_edges.insert(edge.id.clone()) {
                edge_ids.push(edge.id.clone());
            }
            if visited.insert(other.to_string()) {
                node_ids.push(other.to_string());
                queue.push_back((other.to_string(), depth + 1));
            }
        }
    }

    Ok(NeighborhoodSelection {
        node_ids,
        edge_ids,
        truncated,
    })
}

fn graph_fingerprint(graph: &Graph) -> Result<String, ReadsideError> {
    validate_graph(graph)?;
    let mut nodes: Vec<&Node> = graph.nodes.iter().collect();
    let mut edges: Vec<&Edge> = graph.edges.iter().collect();
    nodes.sort_by(|a, b| a.id.cmp(&b.id));
    edges.sort_by(|a, b| a.id.cmp(&b.id));

    let mut hasher = Sha256::new();
    hasher.update(b"ebca-graph-readside-fingerprint-v1\0");
    hasher.update(graph.graph_id.as_bytes());
    for node in nodes {
        hasher.update([0]);
        hasher.update(
            serde_json::to_vec(node)
                .map_err(|error| ReadsideError::new(format!("cannot serialize node fingerprint: {error}")))?,
        );
    }
    for edge in edges {
        hasher.update([0]);
        hasher.update(
            serde_json::to_vec(edge)
                .map_err(|error| ReadsideError::new(format!("cannot serialize edge fingerprint: {error}")))?,
        );
    }
    Ok(format!("{:x}", hasher.finalize()))
}

fn query_signature(graph: &Graph, options: &NeighborOptions) -> Result<String, ReadsideError> {
    let mut roots = options.roots.clone();
    let mut relations = options.relations.clone();
    let mut origins = options.origins.clone();
    roots.sort();
    roots.dedup();
    relations.sort();
    relations.dedup();
    origins.sort();
    origins.dedup();

    let mut hasher = Sha256::new();
    hasher.update(b"ebca-neighbor-cursor-v1\0");
    hasher.update(graph_fingerprint(graph)?.as_bytes());
    hasher.update([0]);
    hasher.update(options.direction.label().as_bytes());
    hasher.update([0]);
    hasher.update(options.hops.to_string().as_bytes());
    for value in roots.into_iter().chain(relations).chain(origins) {
        hasher.update([0]);
        hasher.update(value.as_bytes());
    }
    Ok(format!("{:x}", hasher.finalize()))
}

fn parse_cursor(cursor: Option<&str>, signature: &str) -> Result<(usize, usize), ReadsideError> {
    let Some(cursor) = cursor else {
        return Ok((0, 0));
    };
    let parts: Vec<&str> = cursor.split(':').collect();
    if parts.len() != 4 || parts[0] != "v1" || parts[1] != signature {
        return Err(ReadsideError::new("invalid or mismatched continuation cursor"));
    }
    let node_offset = parts[2]
        .parse::<usize>()
        .map_err(|_| ReadsideError::new("invalid continuation cursor node offset"))?;
    let edge_offset = parts[3]
        .parse::<usize>()
        .map_err(|_| ReadsideError::new("invalid continuation cursor edge offset"))?;
    Ok((node_offset, edge_offset))
}

pub fn neighbors(graph: &Graph, options: NeighborOptions) -> Result<NeighborhoodResult, ReadsideError> {
    if options.node_limit == 0 || options.node_limit > MAX_NEIGHBOR_NODE_LIMIT {
        return Err(ReadsideError::new(format!(
            "neighbors node_limit must be 1..{MAX_NEIGHBOR_NODE_LIMIT}"
        )));
    }
    if options.edge_limit == 0 || options.edge_limit > MAX_NEIGHBOR_EDGE_LIMIT {
        return Err(ReadsideError::new(format!(
            "neighbors edge_limit must be 1..{MAX_NEIGHBOR_EDGE_LIMIT}"
        )));
    }

    let selection = select_neighborhood(graph, &options)?;
    if !selection.edge_ids.is_empty() && options.node_limit < 2 {
        return Err(ReadsideError::new(
            "neighbors node_limit must be at least 2 when the selection contains edges",
        ));
    }
    let signature = query_signature(graph, &options)?;
    let (mut node_offset, mut edge_offset) = parse_cursor(options.cursor.as_deref(), &signature)?;
    if node_offset > selection.node_ids.len() || edge_offset > selection.edge_ids.len() {
        return Err(ReadsideError::new("continuation cursor is outside the selected graph window"));
    }

    let validated = validate_graph(graph)?;
    let mut included = HashSet::new();
    let mut returned_edges = Vec::new();

    while edge_offset < selection.edge_ids.len() && returned_edges.len() < options.edge_limit {
        let edge_id = &selection.edge_ids[edge_offset];
        let edge = validated
            .edges
            .get(edge_id.as_str())
            .ok_or_else(|| ReadsideError::new(format!("selected edge disappeared: {edge_id}")))?;
        let mut additions = 0;
        if !included.contains(edge.source.as_str()) {
            additions += 1;
        }
        if edge.target != edge.source && !included.contains(edge.target.as_str()) {
            additions += 1;
        }
        if included.len() + additions > options.node_limit {
            break;
        }
        included.insert(edge.source.clone());
        included.insert(edge.target.clone());
        returned_edges.push((*edge).clone());
        edge_offset += 1;
    }

    while node_offset < selection.node_ids.len() && included.len() < options.node_limit {
        included.insert(selection.node_ids[node_offset].clone());
        node_offset += 1;
    }

    let returned_nodes = selection
        .node_ids
        .iter()
        .filter(|node_id| included.contains(node_id.as_str()))
        .map(|node_id| {
            validated
                .nodes
                .get(node_id.as_str())
                .copied()
                .ok_or_else(|| ReadsideError::new(format!("selected node disappeared: {node_id}")))
                .cloned()
        })
        .collect::<Result<Vec<_>, _>>()?;

    let returned_ids: HashSet<&str> = returned_nodes.iter().map(|node| node.id.as_str()).collect();
    if returned_edges.iter().any(|edge| {
        !returned_ids.contains(edge.source.as_str()) || !returned_ids.contains(edge.target.as_str())
    }) {
        return Err(ReadsideError::new(
            "internal invariant failure: neighborhood would contain a dangling returned edge",
        ));
    }

    let more_nodes = node_offset < selection.node_ids.len();
    let more_edges = edge_offset < selection.edge_ids.len();
    let next_cursor = if more_nodes || more_edges {
        Some(format!("v1:{signature}:{node_offset}:{edge_offset}"))
    } else {
        None
    };

    Ok(NeighborhoodResult {
        graph_id: graph.graph_id.clone(),
        nodes: returned_nodes,
        edges: returned_edges,
        totals: SelectionTotals {
            nodes: selection.node_ids.len(),
            edges: selection.edge_ids.len(),
        },
        truncated: selection.truncated || more_nodes || more_edges,
        selection_truncated: selection.truncated,
        next_cursor,
    })
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct ShortestPathOptions {
    pub source: String,
    pub target: String,
    pub direction: Direction,
    #[serde(default)]
    pub relations: Vec<String>,
    #[serde(default)]
    pub origins: Vec<String>,
    pub max_hops: u8,
    pub max_paths: usize,
    pub expansion_limit: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct GraphPath {
    pub node_ids: Vec<String>,
    pub edge_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct ShortestPathResult {
    pub graph_id: String,
    pub paths: Vec<GraphPath>,
    pub expansions: usize,
    pub truncated: bool,
}

fn path_adjacency<'a>(
    graph: &'a Graph,
    direction: Direction,
    relations: &BTreeSet<&str>,
    origins: &BTreeSet<&str>,
) -> HashMap<&'a str, Vec<&'a Edge>> {
    let mut adjacency: HashMap<&str, Vec<&Edge>> = HashMap::new();
    for edge in &graph.edges {
        if !edge_passes_filters(edge, relations, origins) {
            continue;
        }
        match direction {
            Direction::Out => adjacency.entry(edge.source.as_str()).or_default().push(edge),
            Direction::In => adjacency.entry(edge.target.as_str()).or_default().push(edge),
            Direction::Both => {
                adjacency.entry(edge.source.as_str()).or_default().push(edge);
                if edge.target != edge.source {
                    adjacency.entry(edge.target.as_str()).or_default().push(edge);
                }
            }
        }
    }
    for edges in adjacency.values_mut() {
        edges.sort_by(|a, b| a.id.cmp(&b.id));
    }
    adjacency
}

pub fn shortest_paths(
    graph: &Graph,
    options: ShortestPathOptions,
) -> Result<ShortestPathResult, ReadsideError> {
    let validated = validate_graph(graph)?;
    if !validated.nodes.contains_key(options.source.as_str()) {
        return Err(ReadsideError::new(format!("source node does not exist: {}", options.source)));
    }
    if !validated.nodes.contains_key(options.target.as_str()) {
        return Err(ReadsideError::new(format!("target node does not exist: {}", options.target)));
    }
    if options.max_hops == 0 || options.max_hops > MAX_PATH_HOPS {
        return Err(ReadsideError::new(format!(
            "max_hops must be 1..{MAX_PATH_HOPS}"
        )));
    }
    if options.max_paths == 0 || options.max_paths > MAX_PATHS {
        return Err(ReadsideError::new(format!("max_paths must be 1..{MAX_PATHS}")));
    }
    if options.expansion_limit == 0 || options.expansion_limit > MAX_PATH_EXPANSIONS {
        return Err(ReadsideError::new(format!(
            "expansion_limit must be 1..{MAX_PATH_EXPANSIONS}"
        )));
    }
    if options.source == options.target {
        return Ok(ShortestPathResult {
            graph_id: graph.graph_id.clone(),
            paths: vec![GraphPath {
                node_ids: vec![options.source],
                edge_ids: vec![],
            }],
            expansions: 0,
            truncated: false,
        });
    }

    let relations = filter_set(&options.relations);
    let origins = filter_set(&options.origins);
    let adjacency = path_adjacency(graph, options.direction, &relations, &origins);
    let mut queue = VecDeque::new();
    queue.push_back(GraphPath {
        node_ids: vec![options.source.clone()],
        edge_ids: vec![],
    });
    let mut results = Vec::new();
    let mut expansions = 0;
    let mut shortest_len: Option<usize> = None;
    let mut truncated = false;

    'search: while let Some(path) = queue.pop_front() {
        let depth = path.edge_ids.len();
        if depth >= options.max_hops as usize {
            continue;
        }
        if shortest_len.is_some_and(|length| depth >= length) {
            continue;
        }
        let current = path.node_ids.last().expect("path always contains source");
        for edge in adjacency.get(current.as_str()).into_iter().flatten() {
            if expansions >= options.expansion_limit {
                truncated = true;
                break 'search;
            }
            expansions += 1;
            let Some(next) = neighbor_for(edge, current, options.direction) else {
                continue;
            };
            if path.node_ids.iter().any(|node_id| node_id == next) {
                continue;
            }
            let mut candidate = path.clone();
            candidate.node_ids.push(next.to_string());
            candidate.edge_ids.push(edge.id.clone());
            let candidate_len = candidate.edge_ids.len();

            if next == options.target {
                if shortest_len.is_none() {
                    shortest_len = Some(candidate_len);
                }
                if shortest_len == Some(candidate_len) {
                    results.push(candidate);
                    if results.len() >= options.max_paths {
                        truncated = true;
                        break 'search;
                    }
                }
            } else if shortest_len.is_none() && candidate_len < options.max_hops as usize {
                queue.push_back(candidate);
            }
        }
    }

    results.sort_by(|a, b| a.node_ids.cmp(&b.node_ids).then_with(|| a.edge_ids.cmp(&b.edge_ids)));
    Ok(ShortestPathResult {
        graph_id: graph.graph_id.clone(),
        paths: results,
        expansions,
        truncated,
    })
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ExplainResult {
    pub graph_id: String,
    pub element_type: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub node: Option<Node>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub edge: Option<Edge>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source: Option<Node>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target: Option<Node>,
    pub incident_edges: Vec<Edge>,
    pub truncated: bool,
}

pub fn explain(graph: &Graph, element_id: &str, incident_limit: usize) -> Result<ExplainResult, ReadsideError> {
    let validated = validate_graph(graph)?;
    if incident_limit == 0 || incident_limit > MAX_EXPLAIN_INCIDENT {
        return Err(ReadsideError::new(format!(
            "incident_limit must be 1..{MAX_EXPLAIN_INCIDENT}"
        )));
    }
    if let Some(node) = validated.nodes.get(element_id) {
        let mut incident: Vec<Edge> = graph
            .edges
            .iter()
            .filter(|edge| edge.source == element_id || edge.target == element_id)
            .cloned()
            .collect();
        incident.sort_by(|a, b| a.id.cmp(&b.id));
        let truncated = incident.len() > incident_limit;
        incident.truncate(incident_limit);
        return Ok(ExplainResult {
            graph_id: graph.graph_id.clone(),
            element_type: "node".into(),
            node: Some((*node).clone()),
            edge: None,
            source: None,
            target: None,
            incident_edges: incident,
            truncated,
        });
    }
    if let Some(edge) = validated.edges.get(element_id) {
        let source = validated
            .nodes
            .get(edge.source.as_str())
            .copied()
            .ok_or_else(|| ReadsideError::new("edge source disappeared after validation"))?;
        let target = validated
            .nodes
            .get(edge.target.as_str())
            .copied()
            .ok_or_else(|| ReadsideError::new("edge target disappeared after validation"))?;
        return Ok(ExplainResult {
            graph_id: graph.graph_id.clone(),
            element_type: "edge".into(),
            node: None,
            edge: Some((*edge).clone()),
            source: Some(source.clone()),
            target: Some(target.clone()),
            incident_edges: vec![],
            truncated: false,
        });
    }
    Err(ReadsideError::new(format!("graph element does not exist: {element_id}")))
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct DiffOptions {
    pub limit: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Change<T> {
    pub before: T,
    pub after: T,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct DiffTotals {
    pub added_nodes: usize,
    pub removed_nodes: usize,
    pub changed_nodes: usize,
    pub added_edges: usize,
    pub removed_edges: usize,
    pub changed_edges: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct GraphDiff {
    pub before_graph_id: String,
    pub after_graph_id: String,
    pub added_nodes: Vec<Node>,
    pub removed_nodes: Vec<Node>,
    pub changed_nodes: Vec<Change<Node>>,
    pub added_edges: Vec<Edge>,
    pub removed_edges: Vec<Edge>,
    pub changed_edges: Vec<Change<Edge>>,
    pub totals: DiffTotals,
    pub truncated: bool,
}

pub fn diff(before: &Graph, after: &Graph, options: DiffOptions) -> Result<GraphDiff, ReadsideError> {
    let before_validated = validate_graph(before)?;
    let after_validated = validate_graph(after)?;
    if options.limit == 0 || options.limit > MAX_DIFF_LIMIT {
        return Err(ReadsideError::new(format!("diff limit must be 1..{MAX_DIFF_LIMIT}")));
    }

    let added_nodes_all: Vec<Node> = after_validated
        .nodes
        .iter()
        .filter(|(id, _)| !before_validated.nodes.contains_key(**id))
        .map(|(_, node)| (*node).clone())
        .collect();
    let removed_nodes_all: Vec<Node> = before_validated
        .nodes
        .iter()
        .filter(|(id, _)| !after_validated.nodes.contains_key(**id))
        .map(|(_, node)| (*node).clone())
        .collect();
    let changed_nodes_all: Vec<Change<Node>> = before_validated
        .nodes
        .iter()
        .filter_map(|(id, before_node)| {
            after_validated.nodes.get(id).and_then(|after_node| {
                if *before_node != *after_node {
                    Some(Change {
                        before: (*before_node).clone(),
                        after: (*after_node).clone(),
                    })
                } else {
                    None
                }
            })
        })
        .collect();

    let added_edges_all: Vec<Edge> = after_validated
        .edges
        .iter()
        .filter(|(id, _)| !before_validated.edges.contains_key(**id))
        .map(|(_, edge)| (*edge).clone())
        .collect();
    let removed_edges_all: Vec<Edge> = before_validated
        .edges
        .iter()
        .filter(|(id, _)| !after_validated.edges.contains_key(**id))
        .map(|(_, edge)| (*edge).clone())
        .collect();
    let changed_edges_all: Vec<Change<Edge>> = before_validated
        .edges
        .iter()
        .filter_map(|(id, before_edge)| {
            after_validated.edges.get(id).and_then(|after_edge| {
                if *before_edge != *after_edge {
                    Some(Change {
                        before: (*before_edge).clone(),
                        after: (*after_edge).clone(),
                    })
                } else {
                    None
                }
            })
        })
        .collect();

    let totals = DiffTotals {
        added_nodes: added_nodes_all.len(),
        removed_nodes: removed_nodes_all.len(),
        changed_nodes: changed_nodes_all.len(),
        added_edges: added_edges_all.len(),
        removed_edges: removed_edges_all.len(),
        changed_edges: changed_edges_all.len(),
    };
    let truncated = [
        totals.added_nodes,
        totals.removed_nodes,
        totals.changed_nodes,
        totals.added_edges,
        totals.removed_edges,
        totals.changed_edges,
    ]
    .into_iter()
    .any(|count| count > options.limit);

    Ok(GraphDiff {
        before_graph_id: before.graph_id.clone(),
        after_graph_id: after.graph_id.clone(),
        added_nodes: added_nodes_all.into_iter().take(options.limit).collect(),
        removed_nodes: removed_nodes_all.into_iter().take(options.limit).collect(),
        changed_nodes: changed_nodes_all.into_iter().take(options.limit).collect(),
        added_edges: added_edges_all.into_iter().take(options.limit).collect(),
        removed_edges: removed_edges_all.into_iter().take(options.limit).collect(),
        changed_edges: changed_edges_all.into_iter().take(options.limit).collect(),
        totals,
        truncated,
    })
}
