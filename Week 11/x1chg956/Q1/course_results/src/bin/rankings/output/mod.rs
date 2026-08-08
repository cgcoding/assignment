mod row;

use course_results::StudentRecord;
use row::format_row;

pub(crate) fn print_rankings(records: &[StudentRecord]) {
    println!("Rankings");

    for (index, record) in records.iter().enumerate() {
        println!("{}", format_row(index + 1, record));
    }
}
