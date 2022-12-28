use crate::datatypes::Action;
use pyo3::prelude::*;


#[pyclass]
#[derive(Clone)]
pub struct PyAction {
    #[pyo3(get)]
    pub(super) action: PyActionType,
    #[pyo3(get)]
    pub(super) message: String,
}

#[pyclass]
#[derive(Clone)]
pub enum PyActionType {
    Accept,
    Alert,
    Drop,
}

impl From<Action> for PyAction {
    fn from(action: Action) -> Self {
        match action {
            Action::Accept(x) => PyAction { action: PyActionType::Accept, message: x.join(" ") },
            Action::Alert(x) => PyAction { action: PyActionType::Alert, message: x.join(" ") },
            Action::Drop(x) => PyAction { action: PyActionType::Drop, message: x.join(" ") },
        }
    }
}
