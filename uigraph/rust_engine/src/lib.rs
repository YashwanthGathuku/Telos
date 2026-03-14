//! TELOS Delta Engine — efficient diff tracking for UI snapshots.
//!
//! Compares successive UI snapshots and produces compact deltas
//! describing what changed. This enables the dashboard to show
//! live UI state changes without resending full trees.

mod delta;
mod models;

pub use delta::{ChangeKind, DeltaEngine, UIChange};
pub use models::{UIElement, UISnapshot};

pub mod capture;
pub mod server;
