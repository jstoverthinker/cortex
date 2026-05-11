//! Diff between two timepoints of agent reasoning

use serde::{Deserialize, Serialize};

/// Diff result between two timepoints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Diff {
    /// Agent ID
    pub agent_id: String,

    /// Start timestamp
    pub from_time: String,

    /// End timestamp
    pub to_time: String,

    /// Number of decisions in first period
    pub from_count: usize,

    /// Number of decisions in second period
    pub to_count: usize,

    /// Average confidence in first period
    pub from_avg_confidence: f32,

    /// Average confidence in second period
    pub to_avg_confidence: f32,

    /// Confidence delta (to - from)
    pub confidence_delta: f32,

    /// Tools used in first period (unique)
    pub from_tools: Vec<String>,

    /// Tools used in second period (unique)
    pub to_tools: Vec<String>,

    /// Tools added (in to, not in from)
    pub tools_added: Vec<String>,

    /// Tools removed (in from, not in to)
    pub tools_removed: Vec<String>,

    /// Decision types in first period
    pub from_decision_types: Vec<String>,

    /// Decision types in second period
    pub to_decision_types: Vec<String>,

    /// Sample reasoning snippets from first period
    pub from_reasoning_samples: Vec<String>,

    /// Sample reasoning snippets from second period
    pub to_reasoning_samples: Vec<String>,
}

impl Diff {
    /// Human-readable summary
    pub fn summary(&self) -> String {
        let conf_dir = if self.confidence_delta > 0.0 { "+" } else { "" };
        let tool_change = if !self.tools_added.is_empty() || !self.tools_removed.is_empty() {
            format!(
                " Tools: +{} -{}",
                self.tools_added.len(),
                self.tools_removed.len()
            )
        } else {
            String::new()
        };

        format!(
            "Decisions: {} → {}. Confidence: {}{:.1}%.{}",
            self.from_count,
            self.to_count,
            conf_dir,
            self.confidence_delta * 100.0,
            tool_change
        )
    }
}
