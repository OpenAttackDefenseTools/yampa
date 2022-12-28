use std::fmt::Debug;

use regex::bytes::Regex;

pub mod rule;

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone)]
pub enum Action {
    Accept(Vec<String>),
    Alert(Vec<String>),
    Drop(Vec<String>),
}

pub type Port = u16;
#[derive(Debug)]
pub enum RulePort {
    Specific(Port),
    All
}
#[derive(Debug)]
pub struct RulePorts {
    pub ours: RulePort,
    pub theirs: RulePort
}

#[derive(Debug)]
pub enum Direction {
    InBound(RulePorts),
    OutBound(RulePorts)
}

#[derive(Debug)]
pub enum Matcher {
    SetFlow,
    FlowIsSet,
    Regex(Regex)
}

#[derive(Debug)]
pub struct Rule {
    pub action: Action,
    pub direction: Direction,
    pub matchers: Vec<Matcher>,
}

pub type Rules = Vec<Rule>;
