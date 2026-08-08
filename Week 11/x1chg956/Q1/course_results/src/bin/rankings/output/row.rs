use course_results::StudentRecord;

pub(crate) fn format_row(position: usize, record: &StudentRecord) -> String {
    format!("{position}. {:<8} {}", record.name, record.score)
}
