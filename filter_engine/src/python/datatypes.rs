use crate::datatypes::{Action, ProxyDirection};
use crate::datatypes::Effects;
use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub struct PyEffects {
    #[pyo3(get)]
    pub(super) action: PyActionType,
    #[pyo3(get)]
    pub(super) message: String,
    #[pyo3(get)]
    pub(super) tags: Vec<String>,
    #[pyo3(get)]
    pub(super) flow_sets: Vec<String>,
}

#[pyclass]
#[derive(Clone)]
pub struct PyAction {
    #[pyo3(get)]
    pub(super) action: PyActionType,
    #[pyo3(get)]
    pub(super) message: String,
}

#[pyclass]
#[derive(Clone, Debug)]
pub enum PyActionType {
    Accept,
    Alert,
    Drop,
}

#[pyclass]
#[derive(Clone)]
pub struct PyMetadata {
    #[pyo3(get)]
    pub(crate) inner_port: u16,
    #[pyo3(get)]
    pub(crate) outer_port: u16,
    #[pyo3(get)]
    pub(crate) direction: PyProxyDirection,
}

#[pyclass]
#[derive(Debug, Clone, Copy)]
pub enum PyProxyDirection {
    InBound,
    OutBound,
}

#[pymethods]
impl PyMetadata {
    #[new]
    fn new(inner_port: u16, outer_port: u16, direction: PyProxyDirection) -> Self {
        Self {
            inner_port,
            outer_port,
            direction,
        }
    }
}

impl From<PyProxyDirection> for ProxyDirection {
    fn from(direction: PyProxyDirection) -> Self {
        match direction {
            PyProxyDirection::InBound => ProxyDirection::InBound,
            PyProxyDirection::OutBound => ProxyDirection::OutBound,
        }
    }
}

#[pymethods]
impl PyEffects {
    fn __str__(&self, _py: Python) -> String {
        format!(
            "PyEffects {{action: {:?}, message: {:?}, tags: {:?}, set_flows: {:?},}}",
            &self.action, &self.message, &self.tags, &self.flow_sets
        )
    }
}

impl From<Action> for PyAction {
    fn from(action: Action) -> Self {
        match action {
            Action::Accept(x) => PyAction {
                action: PyActionType::Accept,
                message: x.unwrap_or("".into()),
            },
            Action::Alert(x) => PyAction {
                action: PyActionType::Alert,
                message: x.unwrap_or("".into()),
            },
            Action::Drop(x) => PyAction {
                action: PyActionType::Drop,
                message: x.unwrap_or("".into()),
            },
        }
    }
}

impl From<Effects> for PyEffects {
    fn from(effects: Effects) -> Self {
        let mut message: String = "".into();
        let action = if let Some(a) = effects.action {
            match a {
                Action::Accept(o) => {
                    message = o.unwrap_or(String::new());
                    PyActionType::Accept
                }
                Action::Alert(o) => {
                    message = o.unwrap_or(String::new());
                    PyActionType::Alert
                }
                Action::Drop(o) => {
                    message = o.unwrap_or(String::new());
                    PyActionType::Drop
                }
            }
        } else {
            PyActionType::Accept
        };
        Self {
            action,
            message,
            tags: effects.tags,
            flow_sets: effects.flow_sets,
        }
    }
}
