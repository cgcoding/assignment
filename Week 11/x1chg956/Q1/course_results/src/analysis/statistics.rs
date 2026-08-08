use crate::model::StudentRecord;
use super::classification::{earned_distinction, passed};

#[derive(Debug, PartialEq)]
pub struct CourseSummary {
    pub student_count: usize,
    pub average: f64,
    pub pass_count: usize,
    pub distinction_count: usize,
    pub top_score: Option<u32>,
}

pub(crate) fn summarize(records: &[StudentRecord]) -> CourseSummary {
    let student_count = records.len();
    let total: u32 = records.iter().map(|record| record.score).sum();

    let average = if student_count == 0 {
        0.0
    } else {
        total as f64 / student_count as f64
    };

    let pass_count = records
        .iter()
        .filter(|record| passed(record.score))
        .count();

    let distinction_count = records
        .iter()
        .filter(|record| earned_distinction(record.score))
        .count();

    let top_score = records.iter().map(|record| record.score).max();

    CourseSummary {
        student_count,
        average,
        pass_count,
        distinction_count,
        top_score,
    }
}
