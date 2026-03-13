//! TELOS Delta Engine — efficient diff tracking for UI snapshots.
//!
//! Compares successive UI snapshots and produces compact deltas
//! describing what changed. This enables the dashboard to show
//! live UI state changes without resending full trees.

mod models;
mod delta;

pub use models::{UIElement, UISnapshot};
pub use delta::{DeltaEngine, UIChange, ChangeKind};

pub mod capture;
pub mod server;
