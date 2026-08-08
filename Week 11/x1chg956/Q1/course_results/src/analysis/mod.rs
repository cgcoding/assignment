mod classification;
mod ranking;
mod statistics;

use crate::model::StudentRecord;
use ranking::rank_records;
use statistics::summarize;

pub use statistics::CourseSummary;

pub(crate) fn build_summary(records: &[StudentRecord]) -> CourseSummary {
    summarize(records)
}

pub(crate) fn build_ranking(records: Vec<StudentRecord>) -> Vec<StudentRecord> {
    rank_records(records)
}
