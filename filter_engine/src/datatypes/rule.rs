use super::Rule;
use super::{Action, ProxyDirection, Direction, Effects, Matcher, RulePort, RulePorts};

fn match_ports(rule_ports: &RulePorts, home_port: u16, out_port: u16) -> bool {
    if matches!(
        rule_ports.ours,
        RulePort::Specific(p) if p != home_port)
    {
        false
    } else if matches!(
        rule_ports.theirs,
        RulePort::Specific(p) if p != out_port)
    {
        false
    } else {
        true
    }
}

fn match_direction(
    direction: &Direction,
    connection: ProxyDirection,
    home_port: u16,
    out_port: u16,
) -> bool {
    if let Direction::InBound(rps) = direction {
        matches!(connection, ProxyDirection::InBound) && match_ports(rps, home_port, out_port)
    } else if let Direction::OutBound(rps) = direction {
        matches!(connection, ProxyDirection::OutBound) && match_ports(rps, home_port, out_port)
    } else {
        false
    }
}

impl Rule {
    pub fn new(effects: Effects, direction: Direction, matchers: Vec<Matcher>) -> Rule {
        Rule {
            effects,
            direction,
            matchers,
        }
    }

    pub fn empty() -> Rule {
        Rule {
            effects: Effects {
                action: Some(Action::Accept(Some(String::new()))),
                tags: Vec::new(),
                flow_sets: Vec::new(),
            },
            direction: Direction::InBound(RulePorts {
                ours: RulePort::All,
                theirs: RulePort::All,
            }),
            matchers: Vec::new(),
        }
    }

    pub fn with_effects(self, effects: Effects) -> Rule {
        Rule { effects, ..self }
    }

    pub fn with_action(self, action: Action) -> Rule {
        Rule {
            effects: self.effects.with_action(action),
            ..self
        }
    }

    pub fn with_tags(self, tags: Vec<String>) -> Rule {
        Rule {
            effects: self.effects.with_tags(tags),
            ..self
        }
    }

    pub fn with_flow_sets(self, flow_sets: Vec<String>) -> Rule {
        Rule {
            effects: self.effects.with_flow_sets(flow_sets),
            ..self
        }
    }

    pub fn with_direction(self, direction: Direction) -> Rule {
        Rule { direction, ..self }
    }

    pub fn with_matchers(self, matchers: Vec<Matcher>) -> Rule {
        Rule { matchers, ..self }
    }

    pub fn apply(
        &self,
        data: &[u8],
        home_port: u16,
        out_port: u16,
        direction: ProxyDirection,
        flowbits: &Vec<String>,
    ) -> Option<Effects> {
        if match_direction(&self.direction, direction, home_port, out_port) {
            self.matchers
                .iter()
                .all(|m| match m {
                    Matcher::Regex(r) => r.is_match(data),
                    Matcher::FlowIsSet(s) => flowbits.contains(s),
                })
                .then_some(self.effects.clone())
        } else {
            None
        }
    }
}
