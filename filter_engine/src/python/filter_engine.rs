use std::io;
use std::io::Read;
use std::sync::Arc;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rayon::prelude::*;
use crate::datatypes::{Rules, Effects};
use crate::parser::parse;
use crate::python::PyEffects;
use crate::python::datatypes::PyMetadata;

/// Instance of a Filter Engine
/// Create this using `create_filterengine_from_ruleset`
#[pyclass]
#[derive(Debug)]
pub struct FilterEngine {
    pub(crate) rules: Arc<Rules>,
}

/// Instantiates a new filter_engine from a ruleset string
#[pymethods]
impl FilterEngine {
    /// Apply the filter rules and return a list of Effects.
    fn filter<'a>(&self, py: Python<'a>, metadata: PyMetadata, data: Vec<u8>, flowbits: Vec<String>) -> PyResult<&'a PyAny> {
        let rules = self.rules.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            tokio_rayon::spawn(move || -> Result<PyEffects, _> {
                Ok(rules.par_iter()
                    .filter_map(move |r| r.apply(&data, metadata.inner_port, metadata.outer_port, metadata.direction.into(), &flowbits))
                    .reduce(|| Effects::empty(), |a, b| a + b)
                    .into())
            }).await
        })
    }
}

fn parse_rulestring(ruleset: String) -> Result<Rules, String> {
    let rules_string = ruleset.lines().into_iter()
        .filter(|l| !l.is_empty())
        .filter(|l| !l.trim().starts_with("#"))
        .fold("".to_string(),
              |rules, rule| format!("{} {}", rules, rule));

    parse(rules_string)
}

/// Creates a new `FilterEngine` in an async function (from python).
///
/// You will need to create a task to await this result!
#[pyfunction]
pub fn create_filterengine_from_ruleset(py: Python<'_>, ruleset: String) -> PyResult<&PyAny> {
    pyo3_asyncio::tokio::future_into_py(py, async move {
        tokio_rayon::spawn(move || {
            Ok(FilterEngine {
                rules: Arc::new(parse_rulestring(ruleset).map_err(|s| PyValueError::new_err(s))?)
            })
        }).await
    })
}

#[pyfunction]
pub fn rules_lint(_py: Python<'_>) -> PyResult<()> {
    let stdin = io::stdin();
    let mut input = String::new();
    stdin.lock().read_to_string(&mut input).unwrap();

    parse_rulestring(input).map_err(|s| PyValueError::new_err(s)).map(|_| ())
}
