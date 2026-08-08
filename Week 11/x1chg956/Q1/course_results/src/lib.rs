mod analysis;
mod input;
mod model;

pub use analysis::CourseSummary;
pub use model::StudentRecord;

use analysis::{build_ranking, build_summary};
use input::load_records;

pub fn analyse(input: &str) -> CourseSummary {
    let records = load_records(input);
    build_summary(&records)
}

pub fn rankings(input: &str) -> Vec<StudentRecord> {
    let records = load_records(input);
    build_ranking(records)
}
