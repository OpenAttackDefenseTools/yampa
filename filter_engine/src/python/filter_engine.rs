use std::sync::Arc;
use pyo3::prelude::*;
use rayon::prelude::*;
use crate::datatypes::{Rules, ConnectionDirection, Effects};
use crate::parser::parse;
use crate::python::PyEffects;
use pyo3::intern;

/// Instance of a Filter Engine
/// Create this using `create_filterengine_from_ruleset`
#[pyclass]
#[derive(Debug)]
pub struct FilterEngine {
    pub(crate) rules: Arc<Rules>,
}

#[pymethods]
impl FilterEngine {
    /// Apply the filter rules and return a list of Effects.
    fn filter<'a>(&self, py: Python<'a>, metadata: PyObject, data: Vec<u8>, flowbits: Vec<String>) -> PyResult<&'a PyAny> {
        let (home_port, out_port, direction) = unpack(py, metadata);

        let rules = self.rules.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            tokio_rayon::spawn(move || -> Result<PyEffects, _> {
                Ok(rules.par_iter()
                    .filter_map(move |r| r.apply(&data, home_port, out_port, direction.clone(), &flowbits))
                    .reduce(|| Effects::empty(), |a, b| a + b)
                    .into())
            }).await
        })
    }
}

macro_rules! atos {
    ($py: expr, $pyObj: expr, $attr_name: expr) => {
        $pyObj
            .getattr($py, intern!($py, $attr_name))
            .expect(&format!("unable to get py attribute '{}'", $attr_name))
            .to_string()
    };
}

fn unpack(py: Python<'_>, connection: PyObject) -> (u16, u16, ConnectionDirection) {
    (
        atos!(py, connection, "home_port")
            .parse::<u16>()
            .expect("Invalid home_port"),
        atos!(py, connection, "dst_port")
            .parse::<u16>()
            .expect("Invalid dst_port"),
        match atos!(py, connection, "direction").as_str() {
            "IN" => ConnectionDirection::InBound,
            "OUT" => ConnectionDirection::OutBound,
            _ => panic!("panic at the disco"),
        },
    )
}

#[pyfunction]
pub fn create_filterengine_from_ruleset(py: Python<'_>, ruleset: String) -> PyResult<&PyAny> {
    pyo3_asyncio::tokio::future_into_py(py, async move {
        tokio_rayon::spawn(move || {
            let rules_string = ruleset.lines().into_iter()
                .filter(|l| !l.is_empty())
                .filter(|l| !l.trim().starts_with("#"))
                .fold("".to_string(),
                      |rules, rule| format!("{} {}", rules, rule));

            let rules = parse(rules_string).unwrap();

            Ok(FilterEngine {
                rules: Arc::new(rules)
            })
        }).await
    })
}
