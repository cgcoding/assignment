mod display;

use course_results::analyse;
use display::print_summary;

const DATA: &str = "Asha,78\nBiren,91\nCharu,66\nDev,91\nEsha,84\n";

fn main() {
    let summary = analyse(DATA);
    print_summary(&summary);
}
