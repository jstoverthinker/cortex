//! Query filters for time-travel queries

use serde::{Deserialize, Serialize};

/// Filter for querying decisions
#[derive(Debug, Clone, Default)]
pub struct QueryFilter {
    /// Filter by agent ID
    pub agent_id: Option<String>,

    /// Minimum confidence threshold
    pub min_confidence: Option<f32>,

    /// Maximum confidence threshold
    pub max_confidence: Option<f32>,

    /// Start timestamp (ISO 8601)
    pub start_time: Option<String>,

    /// End timestamp (ISO 8601)
    pub end_time: Option<String>,

    /// Filter by decision type
    pub decision_type: Option<String>,

    /// Limit results
    pub limit: Option<usize>,

    /// Order by (asc/desc)
    pub order: Option<QueryOrder>,
}

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize)]
pub enum QueryOrder {
    #[default]
    Desc,
    Asc,
}

impl QueryFilter {
    /// Create a new filter for a specific agent
    pub fn for_agent(agent_id: impl Into<String>) -> Self {
        Self {
            agent_id: Some(agent_id.into()),
            ..Default::default()
        }
    }

    /// Set time range
    pub fn time_range(mut self, start: impl Into<String>, end: impl Into<String>) -> Self {
        self.start_time = Some(start.into());
        self.end_time = Some(end.into());
        self
    }

    /// Set confidence range
    pub fn confidence_range(mut self, min: f32, max: f32) -> Self {
        self.min_confidence = Some(min);
        self.max_confidence = Some(max);
        self
    }

    /// Low confidence decisions (below 0.5)
    pub fn low_confidence() -> Self {
        Self {
            min_confidence: None,
            max_confidence: Some(0.5),
            ..Default::default()
        }
    }

    /// Set limit
    pub fn limit(mut self, n: usize) -> Self {
        self.limit = Some(n);
        self
    }
}
