//! Main AgentDB implementation with SQLite backend

use crate::{CortexError, Decision, DecisionRecord, Diff, QueryFilter, Result};
use chrono::{DateTime, Utc};
use rusqlite::{params, Connection};

/// The main Cortex database handle
pub struct AgentDB {
    conn: Connection,
    path: String,
}

impl AgentDB {
    /// Open or create a Cortex database at the given path
    pub fn open(path: &str) -> Result<Self> {
        let conn = Connection::open(path)?;

        // Enable WAL mode for better concurrency
        conn.execute_batch(
            "
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous = NORMAL;
            ",
        )?;

        // Create tables
        conn.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT NOT NULL,
                tools_used TEXT NOT NULL DEFAULT '[]',
                metadata TEXT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_decisions_agent ON decisions(agent_id);
            CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp);
            CREATE INDEX IF NOT EXISTS idx_decisions_agent_timestamp ON decisions(agent_id, timestamp);
            ",
        )?;

        Ok(Self {
            conn,
            path: path.to_string(),
        })
    }

    /// Record a decision
    pub fn record(&self, decision: Decision) -> Result<i64> {
        let record = DecisionRecord::from_decision(decision);
        let timestamp = record.timestamp.to_rfc3339();

        self.conn.execute(
            "
            INSERT INTO decisions (agent_id, decision, confidence, reasoning, tools_used, metadata, timestamp)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)
            ",
            params![
                record.agent_id,
                record.decision,
                record.confidence,
                record.reasoning,
                record.tools_used,
                record.metadata,
                timestamp,
            ],
        )?;

        Ok(self.conn.last_insert_rowid())
    }

    /// Query decisions with a filter
    pub fn query(&self, filter: &QueryFilter) -> Result<Vec<Decision>> {
        let mut sql = String::from("SELECT id, agent_id, decision, confidence, reasoning, tools_used, metadata, timestamp FROM decisions WHERE 1=1");
        let mut bind_params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

        if let Some(ref agent_id) = filter.agent_id {
            sql.push_str(" AND agent_id = ?");
            bind_params.push(Box::new(agent_id.clone()));
        }

        if let Some(ref start) = filter.start_time {
            sql.push_str(" AND timestamp >= ?");
            bind_params.push(Box::new(start.clone()));
        }

        if let Some(ref end) = filter.end_time {
            sql.push_str(" AND timestamp <= ?");
            bind_params.push(Box::new(end.clone()));
        }

        if let Some(min) = filter.min_confidence {
            sql.push_str(" AND confidence >= ?");
            bind_params.push(Box::new(min));
        }

        if let Some(max) = filter.max_confidence {
            sql.push_str(" AND confidence <= ?");
            bind_params.push(Box::new(max));
        }

        if let Some(ref decision_type) = filter.decision_type {
            sql.push_str(" AND decision = ?");
            bind_params.push(Box::new(decision_type.clone()));
        }

        // Order
        match filter.order {
            None | Some(crate::QueryOrder::Desc) => sql.push_str(" ORDER BY timestamp DESC"),
            Some(crate::QueryOrder::Asc) => sql.push_str(" ORDER BY timestamp ASC"),
        }

        // Limit
        if let Some(limit) = filter.limit {
            sql.push_str(&format!(" LIMIT {}", limit));
        }

        let params: Vec<&dyn rusqlite::ToSql> = bind_params.iter().map(|p| p.as_ref()).collect();

        let mut stmt = self.conn.prepare(&sql)?;
        let records = stmt.query_map(params.as_slice(), |row| {
            Ok(DecisionRecord {
                id: row.get(0)?,
                agent_id: row.get(1)?,
                decision: row.get(2)?,
                confidence: row.get(3)?,
                reasoning: row.get(4)?,
                tools_used: row.get(5)?,
                metadata: row.get(6)?,
                timestamp: row.get::<_, String>(7)?.parse().unwrap_or_else(|_| Utc::now()),
            })
        })?;

        let mut decisions = Vec::new();
        for record in records {
            decisions.push(record?.to_decision());
        }

        Ok(decisions)
    }

    /// Query decisions for an agent within a time range
    pub fn query_time_range(
        &self,
        agent_id: &str,
        start: &str,
        end: &str,
    ) -> Result<Vec<Decision>> {
        self.query(
            &QueryFilter::for_agent(agent_id)
                .time_range(start, end)
                .limit(1000),
        )
    }

    /// Diff agent reasoning between two timepoints
    pub fn diff(&self, agent_id: &str, from_time: &str, to_time: &str) -> Result<Diff> {
        use std::collections::HashSet;

        let from_decisions = self.query_time_range(agent_id, from_time, to_time)?;
        // For "to" period, we'd need a separate time range
        // Simplified: compare from_time..midpoint vs midpoint..to_time
        // For MVP, just return basic stats

        let from_count = from_decisions.len();
        let from_avg_confidence = if from_count > 0 {
            from_decisions.iter().map(|d| d.confidence).sum::<f32>() / from_count as f32
        } else {
            0.0
        };

        let from_tools: HashSet<String> = from_decisions
            .iter()
            .flat_map(|d| d.tools_used.clone())
            .collect();

        let from_decision_types: Vec<String> = from_decisions
            .iter()
            .map(|d| d.decision.clone())
            .collect();

        let from_reasoning_samples: Vec<String> = from_decisions
            .iter()
            .take(3)
            .map(|d| d.reasoning.chars().take(100).collect())
            .collect();

        // Placeholder for "to" period (would be separate query in real impl)
        Ok(Diff {
            agent_id: agent_id.to_string(),
            from_time: from_time.to_string(),
            to_time: to_time.to_string(),
            from_count,
            to_count: 0, // Would be calculated
            from_avg_confidence,
            to_avg_confidence: 0.0, // Would be calculated
            confidence_delta: 0.0,  // Would be calculated
            from_tools: from_tools.into_iter().collect(),
            to_tools: vec![],
            tools_added: vec![],
            tools_removed: vec![],
            from_decision_types,
            to_decision_types: vec![],
            from_reasoning_samples,
            to_reasoning_samples: vec![],
        })
    }

    /// Get database path
    pub fn path(&self) -> &str {
        &self.path
    }

    /// Execute raw SQL query
    pub fn raw_query(&self, sql: &str) -> Result<Vec<serde_json::Value>> {
        let mut stmt = self.conn.prepare(sql)?;
        let rows = stmt.query_map([], |row| {
            let mut obj = serde_json::Map::new();
            for i in 0..row.column_count() {
                let name = row.column_name(i)?.to_string();
                let value: rusqlite::types::Value = row.get(i)?;
                obj.insert(name, value_to_json(value));
            }
            Ok(serde_json::Value::Object(obj))
        })?;

        let mut results = Vec::new();
        for row in rows {
            results.push(row?);
        }
        Ok(results)
    }
}

fn value_to_json(value: rusqlite::types::Value) -> serde_json::Value {
    use rusqlite::types::Value;
    match value {
        Value::Null => serde_json::Value::Null,
        Value::Integer(i) => serde_json::Value::Number(i.into()),
        Value::Real(r) => {
            serde_json::Number::from_f64(r)
                .map(serde_json::Value::Number)
                .unwrap_or(serde_json::Value::Null)
        }
        Value::Text(t) => serde_json::Value::String(t),
        Value::Blob(b) => serde_json::Value::Array(
            b.iter()
                .map(|&v| serde_json::Value::Number(v.into()))
                .collect(),
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_record_and_query() {
        let db = AgentDB::open(":memory:").unwrap();

        db.record(Decision {
            agent_id: "test-agent".into(),
            decision: "test_action".into(),
            confidence: 0.9,
            reasoning: "Test reasoning".into(),
            tools_used: vec!["tool1".into()],
            metadata: None,
        })
        .unwrap();

        let decisions = db.query(&QueryFilter::for_agent("test-agent")).unwrap();
        assert_eq!(decisions.len(), 1);
        assert_eq!(decisions[0].agent_id, "test-agent");
    }
}
