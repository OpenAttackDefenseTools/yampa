use std::sync::Arc;
use pyo3::prelude::*;
use rayon::prelude::*;
use crate::datatypes::Rules;
use crate::parser::parse;
use crate::python::PyAction;

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
        let rules = self.rules.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            tokio_rayon::spawn(move || -> Result<Option<PyAction>, _> {
                Ok(rules.par_iter()
                    .filter_map(move |r| r.apply(&data))
                    .max().map(|x| x.into()))
            }).await
        })
    }
}

#[pyfunction]
pub fn create_filterengine_from_ruleset(py: Python<'_>, ruleset: String) -> PyResult<&PyAny> {
    pyo3_asyncio::tokio::future_into_py(py, async move {
        tokio_rayon::spawn(move || {
            let mut rules_string = ruleset.lines().into_iter()
                .filter(|l| !l.is_empty())
                .filter(|l| !l.trim().starts_with("#"))
                .fold("".to_string(),
                      |rules, rule| format!("{} {}", rules, rule));

            rules_string.push('\n');

            let rules = parse(rules_string.as_bytes()).unwrap();

            Ok(FilterEngine {
                rules: Arc::new(rules)
            })
        }).await
    })
}
