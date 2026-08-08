use std::fmt::Display;

pub(crate) fn render_row(label: &str, value: impl Display) -> String {
    format!("{label:<13}: {value}")
}
