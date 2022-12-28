use super::Rule;
use super::{Action, Matcher, Direction, RulePort, RulePorts};

impl Rule {
     pub fn new(action: Action, 
               direction: Direction, 
               matchers: Vec<Matcher>) -> Rule {
        Rule {
            action,
            direction,
            matchers
        }
    }

    pub fn empty() -> Rule {
        Rule {
            action: Action::Drop(Vec::new()),
            direction: Direction::InBound(RulePorts 
                                          { 
                                              ours: RulePort::All, 
                                              theirs: RulePort::All 
                                          }),
            matchers: Vec::new()
        }
    }

    pub fn with_action(self, action: Action) -> Rule {
        Rule {
            action,
            ..self
        }
    }

    pub fn with_direction(self, direction: Direction) -> Rule {
        Rule {
            direction,
            ..self
        }
    }

    pub fn with_matchers(self, matchers: Vec<Matcher>) -> Rule {
        Rule {
            matchers,
            ..self
        }
    }

    pub fn apply(&self, data: &[u8]) -> Option<Action> {
        self.matchers.iter()
            .all(| m | match m {
                Matcher::Regex(r) => r.is_match(data),
                _ => true
            }).then_some(self.action.clone())
    }
}

