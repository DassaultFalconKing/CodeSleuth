use ebca_graph_readside::watermark::{commit_watermark, normalize_subject, session_watermark};

#[test]
fn normalize_subject_matches_codesleuth_contract() {
    assert_eq!(normalize_subject("  FIX:   One\tThing  \nignored body"), "fix: one thing");
}

#[test]
fn commit_watermark_matches_existing_codesleuth_golden_vector() {
    let parent = "1".repeat(40);
    let value = commit_watermark("codesleuth-provenance-v1", "s56", &parent, "  FIX:   One\tThing  \nignored body")
        .expect("valid watermark");
    assert_eq!(value, "s56-099ece38e6a1");
}

#[test]
fn session_watermark_matches_existing_codesleuth_golden_vector_and_is_domain_separated() {
    let head = "2".repeat(40);
    let first = session_watermark("codesleuth-provenance-v1", "agent1", &head, "session-a")
        .expect("valid session watermark");
    assert_eq!(first, "agent1-5e0cf5e39196");

    let other_session = session_watermark("codesleuth-provenance-v1", "agent1", &head, "session-b")
        .expect("valid session watermark");
    assert_eq!(other_session, "agent1-eb1ef412881b");

    let other_domain = session_watermark("another-project-provenance-v1", "agent1", &head, "session-a")
        .expect("valid session watermark");
    assert_ne!(other_domain, first);
}

#[test]
fn watermark_validation_fails_closed() {
    assert!(commit_watermark("", "s56", &"1".repeat(40), "x").is_err());
    assert!(commit_watermark("domain", "Bad Actor", &"1".repeat(40), "x").is_err());
    assert!(commit_watermark("domain", "actor", "abc", "x").is_err());
    assert!(commit_watermark("domain", "actor", &"1".repeat(40), "   ").is_err());
}
