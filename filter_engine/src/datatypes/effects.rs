use itertools::Itertools;
use std::cmp::max;
use std::ops::Add;

use super::{Action, Effect, Effects};

impl Add for Effects {
    type Output = Effects;

    /// Joins two effects together.
    ///
    /// The tags and flow_sets will be merged like a set union and the 'worse'
    /// actin (`Drop` > `Alert` > `Accept`) will be chosen
    fn add(self, rhs: Self) -> Self::Output {
        let mut tags = self.tags.clone();
        tags.append(&mut rhs.tags.clone());
        let tags: Vec<String> = tags.into_iter().unique().collect();

        let mut flow_sets = self.flow_sets.clone();
        flow_sets.append(&mut rhs.flow_sets.clone());
        let flow_sets: Vec<String> = flow_sets.into_iter().unique().collect();

        Self::Output {
            action: max(self.action, rhs.action),
            tags,
            flow_sets,
        }
    }
}

impl Add<&Effect> for Effects {
    type Output = Effects;

    /// Adds an `Effect` to an existing `Effects` struct
    ///
    /// The tags and flow_sets will be merged like a set union and the 'worse'
    /// actin (`Drop` > `Alert` > `Accept`) will be chosen
    fn add(self, rhs: &Effect) -> Self::Output {
        self + Effects::from(rhs)
    }
}

impl From<&Effect> for Effects {
    /// Maps an `Effect` to an `Effects` struct
    fn from(effect: &Effect) -> Self {
        match effect {
            Effect::Action(a) => Effects::empty().with_action(a.clone()),
            Effect::Tag(tags) => Effects::empty().with_tags(tags.clone()),
            Effect::FlowSet(f) => Effects::empty().with_flow_sets(f.clone()),
        }
    }
}

impl Effects {
    /// Creates a new, empty set of effects
    pub fn empty() -> Self {
        Self {
            action: None,
            tags: Vec::new(),
            flow_sets: Vec::new(),
        }
    }

    /// sets the action for the effects
    pub fn with_action(self, action: Action) -> Self {
        Self {
            action: Some(action),
            ..self
        }
    }

    /// adds tags to the existing tags
    pub fn with_tags(self, add_tags: Vec<String>) -> Self {
        let mut tags = self.tags.clone();
        tags.append(&mut add_tags.clone());
        let tags: Vec<String> = tags.into_iter().unique().collect();

        Self { tags, ..self }
    }

    /// adds flow strings to the existing flow strings
    pub fn with_flow_sets(self, add_flow_sets: Vec<String>) -> Self {
        let mut flow_sets = self.flow_sets.clone();
        flow_sets.append(&mut add_flow_sets.clone());
        let flow_sets: Vec<String> = flow_sets.into_iter().unique().collect();

        Self { flow_sets, ..self }
    }
}
