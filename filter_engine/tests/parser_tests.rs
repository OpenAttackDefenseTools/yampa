#[cfg(test)]
mod tests {
    use std::vec;

    use rust_filter_engine::datatypes::Action;

    use rust_filter_engine::parser::{parse_drop, 
        parse_accept, 
        parse_alert};

    #[test]
    fn parse_drop_positive() {
        let (_, action) = parse_drop(b"DROP")
            .expect("parser error");

        assert_eq!(action, Action::Drop);
    }

    #[test]
    fn parse_drop_negative() {
        parse_drop(b"drop")
            .expect_err("Lowercase drop should not be accepted");
    }

    #[test]
    fn parse_alert_positive() {
        let (_, action) = parse_alert(br#"ALERT("abc", "de\"f" )"#)
            .expect("parser error");

        assert_eq!(action, Action::Alert(vec!["abc".to_string(), r#"de\"f"#.to_string()]));
    }
    

    #[test]
    fn parse_alert_negative() {
        parse_alert(b"alert")
            .expect_err("alert should contain tags");
    }

    #[test]
    fn parse_accept_positive() {
        let (_, action) = parse_accept(b"ACCEPT")
            .expect("parser error");

        assert_eq!(action, Action::Accept);
    }

    #[test]
    fn parse_accept_negative() {
        parse_accept(b"accept")
            .expect_err("Lowercase drop should not be accepted");
    }
}
