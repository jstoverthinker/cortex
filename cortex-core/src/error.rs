//! Error types for Cortex

use thiserror::Error;

#[derive(Error, Debug)]
pub enum CortexError {
    #[error("SQLite error: {0}")]
    Sqlite(#[from] rusqlite::Error),

    #[error("Invalid timestamp format: {0}")]
    InvalidTimestamp(String),

    #[error("Agent not found: {0}")]
    AgentNotFound(String),

    #[error("No decisions found for agent '{agent}' in range {start}..{end}")]
    NoDecisionsInRange { agent: String, start: String, end: String },

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, CortexError>;
