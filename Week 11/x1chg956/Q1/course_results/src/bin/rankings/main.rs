mod output;

use course_results::rankings;
use output::print_rankings;

const DATA: &str = "Asha,78\nBiren,91\nCharu,66\nDev,91\nEsha,84\n";

fn main() {
    let records = rankings(DATA);
    print_rankings(&records);
}
