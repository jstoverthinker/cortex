//! Cortex - SQLite for AI Agents
//!
//! A single-file database that records agent reasoning and enables
//! time-travel queries, diff views, and debugging.
//!
//! # Example
//!
//! ```no_run
//! use cortex_core::{AgentDB, Decision};
//!
//! let db = AgentDB::open("./agent-trace.cortex")?;
//!
//! // Record a decision
//! db.record(Decision {
//!     agent_id: "flight-bot-1".into(),
//!     decision: "book_flight".into(),
//!     confidence: 0.87,
//!     reasoning: "User wants JFK→SFO, cheapest option is $312".into(),
//!     tools_used: vec!["search_flights".into(), "get_price".into()],
//!     metadata: None,
//! })?;
//!
//! // Query by time range
//! let decisions = db.query_time_range("flight-bot-1", "2026-05-08 10:00", "2026-05-08 12:00")?;
//!
//! // Diff between timepoints
//! let diff = db.diff("flight-bot-1", "2026-05-01", "2026-05-08")?;
//! println!("Confidence change: {}%", diff.confidence_delta);
//! ```

mod db;
mod decision;
mod diff;
mod error;
mod query;

pub use db::AgentDB;
pub use decision::Decision;
pub use diff::Diff;
pub use error::{CortexError, Result};
pub use query::QueryFilter;

/// Re-exports for convenience
pub mod prelude {
    pub use crate::{AgentDB, Decision, Diff, QueryFilter};
}
