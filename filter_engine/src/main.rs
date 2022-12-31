use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use std::sync::Arc;

use rayon::prelude::{IntoParallelRefIterator, ParallelIterator};
use rust_filter_engine::datatypes::Effects;
use rust_filter_engine::parser::{
    parse, parse_effect, parse_effects, parse_matchers, parse_matchers_list, parse_quoted,
    parse_rule, parse_rules,
};

use std::sync::mpsc::channel;

fn main() {
    let path = Path::new("./example_rules.rls");

    let file = File::open(&path).unwrap();
    let lines = BufReader::new(file).lines();

    let rules_string = lines
        .into_iter()
        .filter(|l| l.is_ok())
        .map(|l| l.unwrap())
        .filter(|l| !l.is_empty())
        .filter(|l| !l.trim().starts_with("#"))
        .fold("".to_string(), |rules, rule| format!("{} {}", rules, rule));

    let rules = parse(rules_string).unwrap();
    dbg!("{}", &rules);

    let data = b";asldkjf;ldfFLAG{sadfwe};alslkdjf;l";

    let a: Effects = rules
        .par_iter()
        .filter_map(|r| r.apply(data))
        .reduce(|| Effects::empty(), |a, b| a + b);

    dbg!("{}", a);
}
