use std::fmt::Debug;

use regex::bytes::Regex;

pub mod effects;
pub mod rule;

/// Represents a single effect, being either an `Action`, a `Tag`, or a `FlowSet`
#[derive(Debug)]
pub enum Effect {
    Action(Action),
    Tag(Vec<String>),
    FlowSet(Vec<String>),
}

/// Represents the sum of effects for one rule.
///
/// A rule can have multiple tags and flow_sets (also given by multiple) 'TAG'
/// or 'FLOWS' directives, however only a single action may be performed by a
/// rule.
///
/// # Combining Effects
/// To make combining effects easier, this struct implements the `Add` trait
/// for itself and for an `Effect` as the rhs. When adding, the tags and flow
/// strings will be unioned and the 'worse' action will be choosen by
/// `Drop` > `Alert` > `Accept`
#[derive(Debug, Clone)]
pub struct Effects {
    pub action: Option<Action>,
    pub tags: Vec<String>,
    pub flow_sets: Vec<String>,
}

/// Represents one action of a rule with the optional message that will be logged
#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone)]
pub enum Action {
    Accept(Option<String>),
    Alert(Option<String>),
    Drop(Option<String>),
}

/// Type for a port
pub type Port = u16;

/// Represents the options how a port may be specified in a rule. This can
/// either be `All`, as in all ports match, or `Specific` in which case only the
/// specified port will match the rule
#[derive(Debug)]
pub enum RulePort {
    Specific(Port),
    All,
}

/// Represents the two port settings that are important for a rule.
#[derive(Debug)]
pub struct RulePorts {
    pub ours: RulePort,
    pub theirs: RulePort,
}

/// Represents the direction of a rule. A direction also includes the port as
/// a `RulePorts` struct
#[derive(Debug)]
pub enum Direction {
    InBound(RulePorts),
    OutBound(RulePorts),
}

/// Represents just the direction
#[derive(Debug, Clone)]
pub enum ProxyDirection {
    InBound,
    OutBound,
}

/// Represents the options for 'matchers' atm `Regex` or `FlowIsSet` which will
/// trigger the execution of the rule if all of them match
#[derive(Debug)]
pub enum Matcher {
    FlowIsSet(String),
    Regex(Regex),
}

/// Represents a rule.
#[derive(Debug)]
pub struct Rule {
    pub effects: Effects,
    pub direction: Direction,
    pub matchers: Vec<Matcher>,
}

pub type Rules = Vec<Rule>;
