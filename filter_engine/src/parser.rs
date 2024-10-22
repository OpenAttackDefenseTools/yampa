use nom::character::complete::{anychar, digit0};
use regex::bytes::Regex;

use nom::branch::alt;
use nom::bytes::complete::{escaped, tag, take_while};
use nom::character::complete::{none_of, space1};
use nom::combinator::opt;
use nom::error::{convert_error, make_error, ErrorKind, VerboseError};
use nom::multi::separated_list0;
use nom::sequence::{delimited, tuple};
use nom::{Err, Finish, IResult};

use crate::datatypes::Action;
use crate::datatypes::Direction;
use crate::datatypes::Effect;
use crate::datatypes::Effects;
use crate::datatypes::Matcher;
use crate::datatypes::Rule;
use crate::datatypes::RulePort;
use crate::datatypes::RulePorts;
use crate::datatypes::Rules;

/// Parses a string containing several rules into a List of rules
///
/// # Arguments
/// * `rules_string` a long string with the rules separated by a ';'
///
/// # Returns
/// A result with the rules or an error string
pub fn parse(rules_string: String) -> Result<Rules, String> {
    let (s, f): (Vec<_>, Vec<_>) = rules_string.trim()
        .split_inclusive(|c| c == ';')
        .map(|rs| rs.trim())
        .map(|rs| (rs, parse_rule(rs).finish()))
        .map(|(rs, result)| (rs, result
            .map_err(|e| convert_error(rs, e))))
        .map(|(rs, result)| (rs, result
            .and_then(|(remaining, rule)|
                if remaining == ";" { Ok(rule) }else { Err(format!("Found superfluous data at end: {}\n                 Syntax error: ^---------", remaining)) }
            )))
        .partition(|(_, result)| result.is_ok());

    match f.len() {
        0 => Ok(s.into_iter().map(|(_, r)| r.unwrap()).collect()),

        _ => Err(format!(
            "Error parsing rules: {}",
            f.into_iter()
                .map(|(rs, result)| (rs, result.unwrap_err()))
                .map(|(rule, err)| format!("Error in rule: {}\n{}", rule, err))
                .rfold("".to_string(), |a, b| format!("{}\n{}", a, b))
        )),
    }
}

/// Parses a single rule given as a parser
///
/// This function is intended to be used as a parser in the nom sense, therfore
/// it returns an `IResult`
///
/// # Arguments
/// * `input` the `u8` array reference to the input
///
/// # Returns
/// An IResult containing the unconsumed input and the result of the parsing or
/// an error
pub fn parse_rule(input: &str) -> IResult<&str, Rule, VerboseError<&str>> {
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

/// Parses a space seperated list of effects
pub fn parse_effects(input: &str) -> IResult<&str, Vec<Effect>, VerboseError<&str>> {
    separated_list0(space1, parse_effect)(input)
}

/// Parses one effect, being either an `Action`, `FlowSet`, or a `Tag`
pub fn parse_effect(i: &str) -> IResult<&str, Effect, VerboseError<&str>> {
    alt((parse_action, parse_flows, parse_tags))(i)
}

/// Parses an action, being either `Accept`, `Alert`, or `Drop`
pub fn parse_action(i: &str) -> IResult<&str, Effect, VerboseError<&str>> {
    let (i, e) = alt((parse_drop, parse_alert, parse_accept))(i)?;
    Ok((i, Effect::Action(e)))
}

/// parses the `Drop` action and its optional message
pub fn parse_drop(i: &str) -> IResult<&str, Action, VerboseError<&str>> {
    let (i, (_, opt_tag)) = tuple((
        tag("DROP"),
        opt(delimited(tag("("), parse_quoted, tag(")"))),
    ))(i)?;

    Ok((i, Action::Drop(opt_tag)))
}

/// parses the `Alert` action and its optional message
pub fn parse_alert(i: &str) -> IResult<&str, Action, VerboseError<&str>> {
    let (i, (_, opt_tag)) = tuple((
        tag("ALERT"),
        opt(delimited(tag("("), parse_quoted, tag(")"))),
    ))(i)?;

    Ok((i, Action::Alert(opt_tag)))
}

/// parses the `Accept` action and its optional message
pub fn parse_accept(i: &str) -> IResult<&str, Action, VerboseError<&str>> {
    let (i, (_, opt)) = tuple((
        tag("ACCEPT"),
        opt(delimited(tag("("), parse_quoted, tag(")"))),
    ))(i)?;

    Ok((i, Action::Accept(opt)))
}

/// parses a ',' separated list of quoted strings
fn parse_string_list(i: &str) -> IResult<&str, Vec<String>, VerboseError<&str>> {
    separated_list0(tag(","), delimited(ws, parse_quoted, ws))(i)
}

/// parses a quoted string which may contain escape characters
pub fn parse_quoted(input: &str) -> IResult<&str, String, VerboseError<&str>> {
    let esc = escaped(none_of("\\\""), '\\', anychar);
    //            alt((tag("\""), tag("."),
    //                            tag("{"), tag("}"),
    //                            tag("["), tag("]"),
    //                            tag("^"), tag("$"),
    //                            tag("\\"), tag("*"),
    //                            tag("+"))));

    let esc_or_empty = alt((esc, tag("")));
    let (i, s) = delimited(tag("\""), esc_or_empty, tag("\""))(input)?;

    Ok((i, s.replace("\\\"", "\"").replace("\\\\", "\\")))
}

/// consumes (and parses) whitespace characters from the given input
///
/// this may be replaced by the `space` parser in many situations
fn ws(s: &str) -> IResult<&str, &str, VerboseError<&str>> {
    let whitespace = " \t\r\n";
    take_while(|c| whitespace.contains(c))(s)
}

/// parses a parentheses delimited list of quoted strings
fn pars_action_args(i: &str) -> IResult<&str, Vec<String>, VerboseError<&str>> {
    delimited(tag("("), parse_string_list, tag(")"))(i)
}

/// parses the `Tag` effect and its list of string tags
fn parse_tags(i: &str) -> IResult<&str, Effect, VerboseError<&str>> {
    let (i, (_, args)) = tuple((tag("TAGS"), pars_action_args))(i)?;

    Ok((i, Effect::Tag(args)))
}

/// parses the `FlowSet` effect which sets one or more string flows
fn parse_flows(i: &str) -> IResult<&str, Effect, VerboseError<&str>> {
    let (i, (_, args)) = tuple((tag("FLOWS"), pars_action_args))(i)?;

    Ok((i, Effect::FlowSet(args)))
}

/// parses the direction of the rule, being either `InBound` or `OutBound`
/// and the optional port arguments
fn parse_direction(i: &str) -> IResult<&str, Direction, VerboseError<&str>> {
    delimited(ws, alt((parse_direction_in, parse_direction_out)), ws)(i)
}

/// parses the `InBound` direction
fn parse_direction_in(i: &str) -> IResult<&str, Direction, VerboseError<&str>> {
    let (i, (_, opt_ports)) = tuple((tag("IN"), opt(tuple((ws, parse_direction_args)))))(i)?;

    let ports = opt_ports.map(|(_, p)| p).unwrap_or(RulePorts {
        ours: RulePort::All,
        theirs: RulePort::All,
    });

    Ok((i, Direction::InBound(RulePorts { ..ports })))
}

/// parses the `OutBound` direction
fn parse_direction_out(i: &str) -> IResult<&str, Direction, VerboseError<&str>> {
    let (i, (_, opt_ports)) = tuple((tag("OUT"), opt(tuple((ws, parse_direction_args)))))(i)?;

    let ports = opt_ports.map(|(_, p)| p).unwrap_or(RulePorts {
        ours: RulePort::All,
        theirs: RulePort::All,
    });

    Ok((i, Direction::OutBound(RulePorts { ..ports })))
}

/// parses the argument list of the directions
///
/// This can be, if present, `(home_port)` or `(home_port, out_port)`
fn parse_direction_args(i: &str) -> IResult<&str, RulePorts, VerboseError<&str>> {
    let brace_list = delimited(tag("("), parse_port_tuple, tag(")"));

    delimited(ws, brace_list, ws)(i)
}

/// Parses a base ten number into a `u16` (for use in port parsing)
fn parse_base_ten(i: &str) -> IResult<&str, u16, VerboseError<&str>> {
    let (i, dgs) = digit0(i)?;

    Ok((i, dgs.parse().unwrap()))
}

/// parses a port with optional whitespaces
fn parse_port_number(i: &str) -> IResult<&str, u16, VerboseError<&str>> {
    let (i, p) = delimited(ws, parse_base_ten, ws)(i)?;

    Ok((i, p))
}

/// parses the `home_port` and optionally the `out_port`
fn parse_port_tuple(i: &str) -> IResult<&str, RulePorts, VerboseError<&str>> {
    let (i, (our_port, their_port)) =
        tuple((parse_port_number, opt(tuple((tag(","), parse_port_number)))))(i)?;

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

/// parses a parentheses delimited, space separated list of matchers
pub fn parse_matchers(i: &str) -> IResult<&str, Vec<Matcher>, VerboseError<&str>> {
    delimited(tag("("), parse_matchers_list, tag(")"))(i)
}

/// parses a space separated list of matchers
pub fn parse_matchers_list(i: &str) -> IResult<&str, Vec<Matcher>, VerboseError<&str>> {
    let parse_quoted_matcher = |i| {
        let (i, m) = parse_quoted(i)?;

        if let Ok(r) = Regex::new(&m) {
            Ok((i, Matcher::Regex(r)))
        } else {
            Err(Err::Failure(make_error(i, ErrorKind::Fail)))
        }
    };

    let parse_flow_set = |i| {
        let (i, (_, s)) = tuple((tag("SET"), delimited(tag("("), parse_quoted, tag(")"))))(i)?;
        Ok((i, Matcher::FlowIsSet(s)))
    };

    let parse_matcher = alt((parse_quoted_matcher, parse_flow_set));

    separated_list0(space1, parse_matcher)(i)
}
