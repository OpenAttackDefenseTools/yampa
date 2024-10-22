pub mod datatypes;
pub mod parser;
pub mod python;

use pyo3::prelude::*;

use python::*;

/// Setup function for the pymodule.
///
/// Adds the `PyEffects`, `PyActionType` and `FilterEngine` classes, and the
/// `create_filterengine_from_ruleset` function to be available from python
#[pymodule]
fn filter_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_filterengine_from_ruleset, m)?)?;
    m.add_function(wrap_pyfunction!(rules_lint, m)?)?;

    m.add_class::<PyEffects>()?;
    m.add_class::<PyAction>()?;
    m.add_class::<PyActionType>()?;
    m.add_class::<PyMetadata>()?;
    m.add_class::<PyProxyDirection>()?;
    m.add_class::<FilterEngine>()?;

    Ok(())
}
