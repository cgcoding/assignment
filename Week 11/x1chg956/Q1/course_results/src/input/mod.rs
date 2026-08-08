mod parser;

use crate::model::StudentRecord;
use parser::parse_records;

pub(crate) fn load_records(input: &str) -> Vec<StudentRecord> {
    parse_records(input)
}
