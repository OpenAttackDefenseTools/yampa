use std::fs::File;
use std::io::{BufReader, BufRead};
use std::path::Path;

use rayon::prelude::{IntoParallelRefIterator, ParallelIterator};
use rust_filter_engine::parser::{parse, parse_quoted};

use std::sync::mpsc::channel;


fn main() {
    let path = Path::new("./example_rules.rls");

    let file = File::open(&path).unwrap();
    let lines = BufReader::new(file).lines();

    let mut rules_string = lines.into_iter()
        .filter(|l| l.is_ok())
        .map(|l| l.unwrap())
        .filter(|l| !l.is_empty())
        .filter(|l| !l.trim().starts_with("#"))
        .fold("".to_string(), 
              |rules, rule| format!("{} {}", rules, rule));

    rules_string.push('\n');

    let rules = parse(rules_string.as_bytes()).unwrap();

    let data = b";asldkjf;ldfFLAG{sadfwe};alslkdjf;l";

    let a = rules.par_iter()
        .filter_map(move |r| r.apply(data))
        .max();

    dbg!("{}", a);
}
