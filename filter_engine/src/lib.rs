pub mod datatypes;
pub mod parser;
mod python;

use pyo3::prelude::*;

#[pymodule]
fn filter_engine(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    pyo3_log::init();

    m.add_function(wrap_pyfunction!(python::create_filterengine_from_ruleset, m)?)?;
    m.add_class::<python::FilterEngine>()?;
    m.add_class::<python::PyAction>()?;
    m.add_class::<python::PyActionType>()?;
    Ok(())
}
