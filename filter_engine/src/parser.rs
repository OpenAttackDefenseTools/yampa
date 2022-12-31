use std::u8;

use nom::character::complete::anychar;
use regex::bytes::Regex;

use nom::branch::alt;
use nom::bytes::complete::{escaped, take_while};
use nom::bytes::streaming::tag;
use nom::character::streaming::{none_of, space1};
use nom::character::{is_digit, is_space};
use nom::combinator::opt;
use nom::error::{make_error, ErrorKind};
use nom::multi::separated_list0;
use nom::sequence::{delimited, tuple};
use nom::{Err, IResult};

use crate::datatypes::Action;
use crate::datatypes::Direction;
use crate::datatypes::Effect;
use crate::datatypes::Effects;
use crate::datatypes::Matcher;
use crate::datatypes::Rule;
use crate::datatypes::RulePort;
use crate::datatypes::RulePorts;
use crate::datatypes::Rules;

pub fn parse(rules_string: String) -> Result<Rules, String> {
    let (s, f): (Vec<_>, Vec<_>) = rules_string
        .split_inclusive(|c| c == ';')
        .map(|rs| rs.trim().as_bytes())
        .map(|rs| (rs, parse_rule(rs)))
        .partition(|(_, result)| result.is_ok());

    match f.len() {
        0 => Ok(s
            .into_iter()
            .map(|(_, r)| r)
            .filter_map(|x| if let Ok((_, r)) = x { Some(r) } else { None })
            .collect()),

        _ => Err(format!(
            "Error parsing rules: {}",
            f.into_iter()
                .map(|(st, _)| String::from_utf8(st.to_vec()).unwrap())
                .rfold("".to_string(), |a, b| format!("{} \n {}", a, b))
        )),
    }
}

pub fn parse_rules(input: &[u8]) -> IResult<&[u8], Vec<Rule>> {
    let (i, rs) = separated_list0(tag(";"), parse_rule)(input)?;

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
    let (i, (effects, _, _, direction, _, _, matchers)) = tuple((
        parse_effects,
        ws,
        tag(":"),
        parse_direction,
        tag(":"),
        ws,
        parse_matchers_list,
    ))(input)?;

    effects.iter().rfold(Effects::empty(), |a, e| a + e);

    Ok((
        i,
        Rule::empty()
            .with_effects(effects.iter().rfold(Effects::empty(), |a, e| a + e))
            .with_direction(direction)
            .with_matchers(matchers),
    ))
}

pub fn parse_effects(input: &[u8]) -> IResult<&[u8], Vec<Effect>> {
    separated_list0(space1, parse_effect)(input)
}

pub fn parse_effect(i: &[u8]) -> IResult<&[u8], Effect> {
    alt((parse_action, parse_flows, parse_tags))(i)
}

pub fn parse_action(i: &[u8]) -> IResult<&[u8], Effect> {
    let (i, e) = alt((parse_drop, parse_alert, parse_accept))(i)?;
    Ok((i, Effect::Action(e)))
}

pub fn parse_drop(i: &[u8]) -> IResult<&[u8], Action> {
    let (i, (_, opt_tag)) = tuple((
        tag("DROP"),
        opt(delimited(tag("("), parse_quoted, tag(")"))),
    ))(i)?;

    Ok((i, Action::Drop(opt_tag)))
}

pub fn parse_alert(i: &[u8]) -> IResult<&[u8], Action> {
    let (i, (_, opt_tag)) = tuple((
        tag("ALERT"),
        opt(delimited(tag("("), parse_quoted, tag(")"))),
    ))(i)?;

    Ok((i, Action::Alert(opt_tag)))
}

pub fn parse_accept(i: &[u8]) -> IResult<&[u8], Action> {
    let (i, (_, opt)) = tuple((
        tag("ACCEPT"),
        opt(delimited(tag("("), parse_quoted, tag(")"))),
    ))(i)?;

    Ok((i, Action::Accept(opt)))
}

fn parse_string_list(i: &[u8]) -> IResult<&[u8], Vec<String>> {
    separated_list0(tag(","), delimited(ws, parse_quoted, ws))(i)
}

pub fn parse_quoted(input: &[u8]) -> IResult<&[u8], String> {
    let esc = escaped(none_of("\\\""), '\\', anychar);
    //            alt((tag("\""), tag("."),
    //                            tag("{"), tag("}"),
    //                            tag("["), tag("]"),
    //                            tag("^"), tag("$"),
    //                            tag("\\"), tag("*"),
    //                            tag("+"))));

    let esc_or_empty = alt((esc, tag("")));
    let (i, s) = delimited(tag("\""), esc_or_empty, tag("\""))(input)?;

    Ok((
        i,
        String::from_utf8(s.to_vec())
            .unwrap()
            .replace("\\\"", "\"")
            .replace("\\\\", "\\"),
    ))
}

fn ws(s: &[u8]) -> IResult<&[u8], &[u8]> {
    //let is_whitespace = |c| is_space(c) || c == b'\n';
    take_while(is_space)(s)
}

fn pars_action_args(i: &[u8]) -> IResult<&[u8], Vec<String>> {
    delimited(tag("("), parse_string_list, tag(")"))(i)
}

fn parse_tags(i: &[u8]) -> IResult<&[u8], Effect> {
    let (i, (_, args)) = tuple((tag("TAGS"), pars_action_args))(i)?;

    Ok((i, Effect::Tag(args)))
}

fn parse_flows(i: &[u8]) -> IResult<&[u8], Effect> {
    let (i, (_, args)) = tuple((tag("FLOWS"), pars_action_args))(i)?;

    Ok((i, Effect::FlowSet(args)))
}

fn parse_direction(i: &[u8]) -> IResult<&[u8], Direction> {
    delimited(ws, alt((parse_direction_in, parse_direction_out)), ws)(i)
}

fn parse_direction_in(i: &[u8]) -> IResult<&[u8], Direction> {
    let (i, (_, opt_ports)) =
        tuple((tag("IN"), opt(tuple((ws, parse_direction_args)))))(i)?;

    let ports = opt_ports.map(|(_, p)| p).unwrap_or(RulePorts {
        ours: RulePort::All,
        theirs: RulePort::All,
    });

    Ok((i, Direction::InBound(RulePorts { ..ports })))
}

fn parse_direction_out(i: &[u8]) -> IResult<&[u8], Direction> {
    let (i, (_, opt_ports)) =
        tuple((tag("OUT"), opt(tuple((ws, parse_direction_args)))))(i)?;

    let ports = opt_ports.map(|(_, p)| p).unwrap_or(RulePorts {
        ours: RulePort::All,
        theirs: RulePort::All,
    });

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
    let (i, p) = delimited(ws, parse_base_ten, ws)(i)?;

    Ok((i, p))
}

fn parse_port_tuple(i: &[u8]) -> IResult<&[u8], RulePorts> {
    let (i, (our_port, their_port)) = tuple((
        parse_port_number,
        opt(tuple((tag(","), parse_port_number))),
    ))(i)?;

    Ok((
        i,
        match their_port {
            Some((_, port)) => RulePorts {
                ours: RulePort::Specific(our_port),
                theirs: RulePort::Specific(port),
            },
            None => RulePorts {
                ours: RulePort::Specific(our_port),
                theirs: RulePort::All,
            },
        },
    ))
}

pub fn parse_matchers(i: &[u8]) -> IResult<&[u8], Vec<Matcher>> {
    delimited(tag("("), parse_matchers_list, tag(")"))(i)
}

pub fn parse_matchers_list(i: &[u8]) -> IResult<&[u8], Vec<Matcher>> {
    let parse_quoted_matcher = |i| {
        let (i, m) = parse_quoted(i)?;

        if let Ok(r) = Regex::new(&m) {
            Ok((i, Matcher::Regex(r)))
        } else {
            Err(Err::Failure(make_error(i, ErrorKind::Fail)))
        }
    };

    let parse_flow_set = |i| {
        let (i, (_, s)) = tuple((
            tag("SET"),
            delimited(tag("("), parse_quoted, tag(")")),
        ))(i)?;
        Ok((i, Matcher::FlowIsSet(s)))
    };

    let parse_matcher = alt((parse_quoted_matcher, parse_flow_set));

    separated_list0(space1, parse_matcher)(i)
}
