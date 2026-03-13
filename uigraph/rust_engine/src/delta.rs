//! Delta computation engine — compares two UI snapshots and produces change events.

use crate::models::{UIElement, UISnapshot};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ChangeKind {
    Added,
    Removed,
    ValueChanged,
    NameChanged,
    Moved,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UIChange {
    pub kind: ChangeKind,
    pub element_key: String,
    pub element_name: String,
    pub control_type: String,
    pub old_value: Option<String>,
    pub new_value: Option<String>,
}

pub struct DeltaEngine {
    previous: Option<UISnapshot>,
}

impl DeltaEngine {
    pub fn new() -> Self {
        Self { previous: None }
    }

    /// Compute delta between the stored previous snapshot and a new one.
    /// Updates the stored snapshot to the new one.
    pub fn compute(&mut self, new_snapshot: UISnapshot) -> Vec<UIChange> {
        let changes = match &self.previous {
            Some(old) => diff_elements(&old.elements, &new_snapshot.elements),
            None => {
                // First snapshot — everything is "added"
                flatten(&new_snapshot.elements)
                    .into_iter()
                    .map(|el| UIChange {
                        kind: ChangeKind::Added,
                        element_key: el.diff_key(),
                        element_name: el.name.clone(),
                        control_type: el.control_type.clone(),
                        old_value: None,
                        new_value: if el.value.is_empty() { None } else { Some(el.value.clone()) },
                    })
                    .collect()
            }
        };
        self.previous = Some(new_snapshot);
        changes
    }

    /// Clear the stored previous snapshot.
    pub fn reset(&mut self) {
        self.previous = None;
    }
}

impl Default for DeltaEngine {
    fn default() -> Self {
        Self::new()
    }
}

fn diff_elements(old: &[UIElement], new: &[UIElement]) -> Vec<UIChange> {
    let mut changes = Vec::new();

    let old_map: HashMap<String, &UIElement> = old.iter().map(|e| (e.diff_key(), e)).collect();
    let new_map: HashMap<String, &UIElement> = new.iter().map(|e| (e.diff_key(), e)).collect();

    // Check for added and changed elements
    for (key, new_el) in &new_map {
        match old_map.get(key) {
            None => {
                changes.push(UIChange {
                    kind: ChangeKind::Added,
                    element_key: key.clone(),
                    element_name: new_el.name.clone(),
                    control_type: new_el.control_type.clone(),
                    old_value: None,
                    new_value: Some(new_el.value.clone()),
                });
            }
            Some(old_el) => {
                if old_el.value != new_el.value && !new_el.is_password {
                    changes.push(UIChange {
                        kind: ChangeKind::ValueChanged,
                        element_key: key.clone(),
                        element_name: new_el.name.clone(),
                        control_type: new_el.control_type.clone(),
                        old_value: Some(old_el.value.clone()),
                        new_value: Some(new_el.value.clone()),
                    });
                }
                if old_el.name != new_el.name {
                    changes.push(UIChange {
                        kind: ChangeKind::NameChanged,
                        element_key: key.clone(),
                        element_name: new_el.name.clone(),
                        control_type: new_el.control_type.clone(),
                        old_value: Some(old_el.name.clone()),
                        new_value: Some(new_el.name.clone()),
                    });
                }

                // Recurse into children
                let child_changes = diff_elements(&old_el.children, &new_el.children);
                changes.extend(child_changes);
            }
        }
    }

    // Check for removed elements
    for (key, old_el) in &old_map {
        if !new_map.contains_key(key) {
            changes.push(UIChange {
                kind: ChangeKind::Removed,
                element_key: key.clone(),
                element_name: old_el.name.clone(),
                control_type: old_el.control_type.clone(),
                old_value: Some(old_el.value.clone()),
                new_value: None,
            });
        }
    }

    changes
}

fn flatten(elements: &[UIElement]) -> Vec<&UIElement> {
    let mut result = Vec::new();
    for el in elements {
        result.push(el);
        if !el.children.is_empty() {
            result.extend(flatten(&el.children));
        }
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::{UIElement, UISnapshot};

    fn make_snapshot(elements: Vec<UIElement>) -> UISnapshot {
        UISnapshot {
            window_title: "Test".into(),
            process_name: "test".into(),
            process_id: 1234,
            timestamp: "2026-01-01T00:00:00Z".into(),
            elements,
        }
    }

    fn make_element(id: &str, name: &str, value: &str) -> UIElement {
        UIElement {
            automation_id: id.into(),
            name: name.into(),
            control_type: "Edit".into(),
            value: value.into(),
            bounding_rect: Default::default(),
            children: vec![],
            is_password: false,
        }
    }

    #[test]
    fn test_first_snapshot_all_added() {
        let mut engine = DeltaEngine::new();
        let snap = make_snapshot(vec![make_element("a", "Field A", "100")]);
        let changes = engine.compute(snap);
        assert_eq!(changes.len(), 1);
        assert_eq!(changes[0].kind, ChangeKind::Added);
    }

    #[test]
    fn test_value_changed() {
        let mut engine = DeltaEngine::new();
        let snap1 = make_snapshot(vec![make_element("a", "Field A", "100")]);
        engine.compute(snap1);

        let snap2 = make_snapshot(vec![make_element("a", "Field A", "200")]);
        let changes = engine.compute(snap2);
        assert_eq!(changes.len(), 1);
        assert_eq!(changes[0].kind, ChangeKind::ValueChanged);
        assert_eq!(changes[0].old_value, Some("100".into()));
        assert_eq!(changes[0].new_value, Some("200".into()));
    }

    #[test]
    fn test_element_removed() {
        let mut engine = DeltaEngine::new();
        let snap1 = make_snapshot(vec![
            make_element("a", "A", "1"),
            make_element("b", "B", "2"),
        ]);
        engine.compute(snap1);

        let snap2 = make_snapshot(vec![make_element("a", "A", "1")]);
        let changes = engine.compute(snap2);
        assert!(changes.iter().any(|c| c.kind == ChangeKind::Removed && c.element_key == "b"));
    }

    #[test]
    fn test_element_added() {
        let mut engine = DeltaEngine::new();
        let snap1 = make_snapshot(vec![make_element("a", "A", "1")]);
        engine.compute(snap1);

        let snap2 = make_snapshot(vec![
            make_element("a", "A", "1"),
            make_element("c", "C", "3"),
        ]);
        let changes = engine.compute(snap2);
        assert!(changes.iter().any(|c| c.kind == ChangeKind::Added && c.element_key == "c"));
    }

    #[test]
    fn test_password_value_not_diffed() {
        let mut engine = DeltaEngine::new();
        let mut pw = make_element("pw", "Password", "secret1");
        pw.is_password = true;
        let snap1 = make_snapshot(vec![pw]);
        engine.compute(snap1);

        let mut pw2 = make_element("pw", "Password", "secret2");
        pw2.is_password = true;
        let snap2 = make_snapshot(vec![pw2]);
        let changes = engine.compute(snap2);
        // Password fields should not produce ValueChanged
        assert!(changes.iter().all(|c| c.kind != ChangeKind::ValueChanged));
    }

    #[test]
    fn test_no_changes() {
        let mut engine = DeltaEngine::new();
        let snap1 = make_snapshot(vec![make_element("a", "A", "1")]);
        engine.compute(snap1);

        let snap2 = make_snapshot(vec![make_element("a", "A", "1")]);
        let changes = engine.compute(snap2);
        assert!(changes.is_empty());
    }
}
