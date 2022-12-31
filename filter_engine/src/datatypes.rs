use std::fmt::Debug;

use regex::bytes::Regex;

pub mod effects;
pub mod rule;

#[derive(Debug)]
pub enum Effect {
    Action(Action),
    Tag(Vec<String>),
    FlowSet(Vec<String>),
}

#[derive(Debug, Clone)]
pub struct Effects {
    pub action: Option<Action>,
    pub tags: Vec<String>,
    pub flow_sets: Vec<String>,
}

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone)]
pub enum Action {
    Accept(Option<String>),
    Alert(Option<String>),
    Drop(Option<String>),
}

pub type Port = u16;
#[derive(Debug)]
pub enum RulePort {
    Specific(Port),
    All,
}
#[derive(Debug)]
pub struct RulePorts {
    pub ours: RulePort,
    pub theirs: RulePort,
}

#[derive(Debug)]
pub enum Direction {
    InBound(RulePorts),
    OutBound(RulePorts),
}

#[derive(Debug, Clone)]
pub enum ConnectionDirection {
    InBound,
    OutBound,
}

#[derive(Debug)]
pub enum Matcher {
    FlowIsSet(String),
    Regex(Regex),
}

#[derive(Debug)]
pub struct Rule {
    pub effects: Effects,
    pub direction: Direction,
    pub matchers: Vec<Matcher>,
}

pub type Rules = Vec<Rule>;
