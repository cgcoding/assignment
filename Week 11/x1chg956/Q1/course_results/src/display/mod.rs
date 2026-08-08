mod table;

use course_results::CourseSummary;
use table::render_row;

pub(crate) fn print_summary(summary: &CourseSummary) {
    println!("Course summary");
    println!("{}", render_row("Students", summary.student_count));
    println!("{}", render_row("Average", format!("{:.1}", summary.average)));
    println!("{}", render_row("Passed", summary.pass_count));
    println!(
        "{}",
        render_row("Distinctions", summary.distinction_count)
    );

    let top_score = summary
        .top_score
        .map(|score| score.to_string())
        .unwrap_or_else(|| String::from("n/a"));

    println!("{}", render_row("Top score", top_score));
}
