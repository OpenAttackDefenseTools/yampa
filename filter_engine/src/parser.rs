use std::u8;

use nom::character::complete::anychar;
use regex::bytes::Regex;

use nom::bytes::complete::{escaped, take_while};
use nom::character::{is_space, is_digit};
use nom::character::streaming::none_of;
use nom::combinator::opt;
use nom::{IResult, Err};
use nom::error::{ErrorKind, make_error};
use nom::sequence::{delimited, tuple};
use nom::multi::separated_list0;
use nom::bytes::streaming::tag;
use nom::branch::alt;

use crate::datatypes::Action;
use crate::datatypes::Direction;
use crate::datatypes::Matcher;
use crate::datatypes::Rule;
use crate::datatypes::RulePorts;
use crate::datatypes::RulePort;
use crate::datatypes::Rules;

pub fn parse(rules_string: &[u8]) -> Result<Rules, String> {
    match parse_rules(rules_string) {
        Ok((_, rules)) => Ok(rules),
        _ => Err("Unable to parse Rules".to_string())
    }
}

pub fn parse_rules(input: &[u8]) -> IResult<&[u8], Vec<Rule>> {
    let (i, rs) = separated_list0(
        tag(";"), 
        delimited(ws,parse_rule, ws))(input)?;
    
    Ok((i, rs))

    //if i.len() == 0 {
    //    Ok((i, rs))
    //} else {
    //    let (i, _) = take_while(|c| c == b'\t' || c == b';' || c == b' ' || c == b'\n')(i)?;

    //    match i.len() {
    //        0 => Ok((i, rs)),
    //        _ => Err(Err::Failure(make_error(i,ErrorKind::Fail)))
    //    }
    //}
}

pub fn parse_rule(input: &[u8]) -> IResult<&[u8], Rule> {
    let (i, (action, _, direction, _, _, _, matchers)) = 
       tuple((parse_action, ws, parse_direction, ws, tag("::"), ws, parse_matchers))(input)?;

    Ok((i, Rule::empty()
        .with_action(action)
        .with_direction(direction)
        .with_matchers(matchers)))
}

pub fn parse_action(i: &[u8]) -> IResult<&[u8], Action> {
    alt((parse_drop, parse_alert, parse_accept))(i)
}

pub fn parse_drop(i: &[u8]) -> IResult<&[u8], Action> {
    let (input, (_, opt_tags)) = 
        tuple((tag("DROP"), opt(tuple((ws, pars_action_args)))))(i)?;

    Ok((input, Action::Drop(opt_tags
                             .map(|(_, tags)| tags)
                             .unwrap_or(Vec::new()))))
}

pub fn parse_alert(i: &[u8]) -> IResult<&[u8], Action> {
    let (input, (_, opt_tags)) = 
        tuple((tag("ALERT"), opt(tuple((ws, pars_action_args)))))(i)?;

    Ok((input, Action::Alert(opt_tags
                             .map(|(_, tags)| tags)
                             .unwrap_or(Vec::new()))))
}

pub fn parse_accept(i: &[u8]) -> IResult<&[u8], Action> {
    let (input, (_, opt_tags)) = 
        tuple((tag("ACCEPT"), opt(tuple((ws, pars_action_args)))))(i)?;

    Ok((input, Action::Accept(opt_tags
                             .map(|(_, tags)| tags)
                             .unwrap_or(Vec::new()))))
}

fn parse_string_list(i: &[u8]) -> IResult<&[u8], Vec<String>> {
    separated_list0(
        tag(","), 
        delimited(ws,  parse_quoted, ws))(i)
}

pub fn parse_quoted(input: &[u8]) -> IResult<&[u8], String> {
    let esc = 
        escaped(
            none_of("\\\""), 
            '\\', 
            anychar);
//            alt((tag("\""), tag("."), 
//                            tag("{"), tag("}"), 
//                            tag("["), tag("]"), 
//                            tag("^"), tag("$"), 
//                            tag("\\"), tag("*"), 
//                            tag("+"))));

    let esc_or_empty = alt((esc, tag("")));
    let (i, s) = delimited(
        tag("\""), 
        esc_or_empty, 
        tag("\""))(input)?;

    Ok((i, String::from_utf8(s.to_vec()).unwrap()
        .replace("\\\"","\"").replace("\\\\", "\\")))
}

fn ws(s: &[u8]) -> IResult<&[u8], &[u8]> {
    //let is_whitespace = |c| is_space(c) || c == b'\n';
    take_while(is_space)(s)
}

fn pars_action_args(i: &[u8]) -> IResult<&[u8], Vec<String>> {
    delimited(tag("("), parse_string_list, tag(")"))(i)
}

fn parse_direction(i: &[u8]) -> IResult<&[u8], Direction> {
    alt((parse_direction_in, parse_direction_out))(i)
}

fn parse_direction_in(i: &[u8]) -> IResult<&[u8], Direction> {
    let (i, (_, opt_ports)) = 
        tuple((tag("IN"), opt(tuple((ws, parse_direction_args)))))(i)?;

    let ports = opt_ports
        .map(|(_, p)| p)
        .unwrap_or(RulePorts { ours: RulePort::All, theirs: RulePort::All });

    Ok((i, Direction::InBound(RulePorts { ..ports })))
}

fn parse_direction_out(i: &[u8]) -> IResult<&[u8], Direction> {
    let (i, (_, opt_ports)) = 
        tuple((tag("OUT"), opt(tuple((ws, parse_direction_args)))))(i)?;

    let ports = opt_ports
        .map(|(_, p)| p)
        .unwrap_or(RulePorts { ours: RulePort::All, theirs: RulePort::All });

    Ok((i, Direction::OutBound(RulePorts { ..ports })))
}

fn parse_direction_args(i: &[u8]) -> IResult<&[u8], RulePorts> {
    let brace_list = delimited(tag("("), parse_port_tuple, tag(")"));

    delimited(ws, brace_list, ws)(i)
}

fn parse_base_ten(i: &[u8]) -> IResult<&[u8], u16> {
    let (i, dgs) = take_while(is_digit)(i)?;

    Ok((i, String::from_utf8(dgs.to_vec()).unwrap().parse().unwrap()))
}

fn parse_port_number(i: &[u8]) -> IResult<&[u8], u16> {
    let (i, p) = delimited(ws, parse_base_ten,ws)(i)?;

    Ok((i, p))
}

fn parse_port_tuple(i: &[u8]) -> IResult<&[u8], RulePorts> {
    let (i, (our_port, their_port)) = tuple(
        (parse_port_number, opt(tuple((tag(","), parse_port_number))))
        )(i)?;

    Ok((i, match their_port {
        Some((_, port)) => RulePorts { 
            ours: RulePort::Specific(our_port),
            theirs: RulePort::Specific(port)
        }, 
        None => RulePorts {
            ours: RulePort::Specific(our_port),
            theirs: RulePort::All
        }
    }))
}

fn parse_matchers(i: &[u8]) -> IResult<&[u8], Vec<Matcher>> {
    delimited(tag("("), parse_matchers_list, tag(")"))(i)
}

fn parse_matchers_list(i: &[u8]) -> IResult<&[u8], Vec<Matcher>> {
    let parse_quoted_matcher = | i | {
        let (i, m) = parse_quoted(i)?;
        
        //let r = Regex::new(&m);

//        println!("{}", m);
//        Ok((i, Matcher::Regex(r)))

        if let Ok(r) = Regex::new(&m) {
            Ok((i, Matcher::Regex(r)))
        } else {
            Err(Err::Failure(make_error(i,ErrorKind::Fail)))
        }
    };

    let parse_flow_set = | i | {
        let (i, _) = tag("flow_set")(i)?;
        Ok((i, Matcher::FlowIsSet))
    };

    let parse_set_flow = | i | {
        let (i, _) = tag("set_flow")(i)?;
        Ok((i, Matcher::SetFlow))
    };

    let parse_matcher = 
        alt((parse_quoted_matcher, parse_flow_set, parse_set_flow));

    let parse_matcher = 
        delimited(ws, parse_matcher, ws);

    separated_list0(
            tag(","), 
            delimited(ws, parse_matcher, ws))(i)
}
