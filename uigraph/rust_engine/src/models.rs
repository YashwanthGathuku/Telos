//! UI element and snapshot models — mirror the C# UIGraph types.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct UIElement {
    pub automation_id: String,
    pub name: String,
    pub control_type: String,
    pub value: String,
    #[serde(default)]
    pub bounding_rect: HashMap<String, i32>,
    #[serde(default)]
    pub children: Vec<UIElement>,
    #[serde(default)]
    pub is_password: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UISnapshot {
    pub window_title: String,
    pub process_name: String,
    pub process_id: i32,
    pub timestamp: String,
    #[serde(default)]
    pub elements: Vec<UIElement>,
}

impl UIElement {
    /// Unique key for diffing — uses automation_id if available, else name+type.
    pub fn diff_key(&self) -> String {
        if !self.automation_id.is_empty() {
            self.automation_id.clone()
        } else {
            format!("{}:{}", self.control_type, self.name)
        }
    }
}
