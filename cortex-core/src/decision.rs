//! Decision types for recording agent actions

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// A recorded agent decision
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Decision {
    /// Unique agent identifier
    pub agent_id: String,

    /// Decision/action name (e.g., "book_flight", "send_email")
    pub decision: String,

    /// Confidence score (0.0 - 1.0)
    pub confidence: f32,

    /// Reasoning/explanation for the decision
    pub reasoning: String,

    /// Tools/functions called during this decision
    pub tools_used: Vec<String>,

    /// Optional metadata (user_id, session, etc.)
    pub metadata: Option<serde_json::Value>,
}

/// Internal representation with auto-generated fields
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct DecisionRecord {
    pub id: i64,
    pub agent_id: String,
    pub decision: String,
    pub confidence: f32,
    pub reasoning: String,
    pub tools_used: String, // JSON array
    pub metadata: Option<String>, // JSON object
    pub timestamp: DateTime<Utc>,
}

impl DecisionRecord {
    pub fn from_decision(decision: Decision) -> Self {
        Self {
            id: 0,
            agent_id: decision.agent_id,
            decision: decision.decision,
            confidence: decision.confidence,
            reasoning: decision.reasoning,
            tools_used: serde_json::to_string(&decision.tools_used).unwrap_or_else(|_| "[]".into()),
            metadata: decision.metadata.map(|m| serde_json::to_string(&m).unwrap_or_else(|_| "{}".into())),
            timestamp: Utc::now(),
        }
    }

    pub fn to_decision(&self) -> Decision {
        Decision {
            agent_id: self.agent_id.clone(),
            decision: self.decision.clone(),
            confidence: self.confidence,
            reasoning: self.reasoning.clone(),
            tools_used: serde_json::from_str(&self.tools_used).unwrap_or_default(),
            metadata: self.metadata.as_ref().and_then(|m| serde_json::from_str(m).ok()),
        }
    }
}
