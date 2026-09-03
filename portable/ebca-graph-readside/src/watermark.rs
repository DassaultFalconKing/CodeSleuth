use sha2::{Digest, Sha256};
use std::error::Error;
use std::fmt::{Display, Formatter};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WatermarkError {
    message: String,
}

impl WatermarkError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

impl Display for WatermarkError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.message)
    }
}

impl Error for WatermarkError {}

pub fn normalize_subject(subject: &str) -> String {
    subject
        .lines()
        .next()
        .unwrap_or_default()
        .trim()
        .to_lowercase()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

fn validate_domain(domain: &str) -> Result<&str, WatermarkError> {
    let value = domain.trim();
    if value.is_empty() || value.len() > 128 || value.chars().any(char::is_control) {
        return Err(WatermarkError::new(
            "domain must be 1..128 non-control characters",
        ));
    }
    Ok(value)
}

fn validate_actor(actor: &str) -> Result<String, WatermarkError> {
    let value = actor.trim().to_lowercase();
    let bytes = value.as_bytes();
    if !(2..=32).contains(&bytes.len()) {
        return Err(WatermarkError::new(
            "actor must be 2..32 lowercase [a-z0-9._-] characters",
        ));
    }
    if !bytes[0].is_ascii_lowercase() && !bytes[0].is_ascii_digit() {
        return Err(WatermarkError::new(
            "actor must start with lowercase ASCII alphanumeric",
        ));
    }
    if !bytes.iter().all(|byte| {
        byte.is_ascii_lowercase() || byte.is_ascii_digit() || matches!(*byte, b'.' | b'_' | b'-')
    }) {
        return Err(WatermarkError::new(
            "actor must be lowercase ASCII [a-z0-9._-]",
        ));
    }
    Ok(value)
}

fn validate_sha(sha: &str) -> Result<String, WatermarkError> {
    let value = sha.trim().to_lowercase();
    if value.len() != 40
        || !value
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
    {
        return Err(WatermarkError::new(
            "SHA must be a full 40-character lowercase Git SHA",
        ));
    }
    Ok(value)
}

fn digest12(payload: &str) -> String {
    let digest = Sha256::digest(payload.as_bytes());
    format!("{:x}", digest)[..12].to_string()
}

pub fn commit_watermark(
    domain: &str,
    actor: &str,
    parent_sha: &str,
    subject: &str,
) -> Result<String, WatermarkError> {
    let domain = validate_domain(domain)?;
    let actor = validate_actor(actor)?;
    let parent_sha = validate_sha(parent_sha)?;
    let normalized = normalize_subject(subject);
    if normalized.is_empty() {
        return Err(WatermarkError::new("commit subject must not be empty"));
    }
    let digest = digest12(&format!(
        "{domain}|commit|{actor}|{parent_sha}|{normalized}"
    ));
    Ok(format!("{actor}-{digest}"))
}

pub fn session_watermark(
    domain: &str,
    actor: &str,
    head_sha: &str,
    session_id: &str,
) -> Result<String, WatermarkError> {
    let domain = validate_domain(domain)?;
    let actor = validate_actor(actor)?;
    let head_sha = validate_sha(head_sha)?;
    let session_id = session_id.trim();
    if session_id.is_empty() || session_id.chars().any(char::is_control) {
        return Err(WatermarkError::new(
            "session id must be non-empty and contain no control characters",
        ));
    }
    let digest = digest12(&format!("{domain}|session|{actor}|{head_sha}|{session_id}"));
    Ok(format!("{actor}-{digest}"))
}
