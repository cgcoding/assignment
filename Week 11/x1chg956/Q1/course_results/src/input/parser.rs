use crate::model::StudentRecord;

pub(crate) fn parse_records(input: &str) -> Vec<StudentRecord> {
    input
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| {
            let (name, score_text) = line
                .split_once(',')
                .expect("each record must contain one comma");

            StudentRecord {
                name: name.trim().to_string(),
                score: score_text
                    .trim()
                    .parse()
                    .expect("score must be an unsigned integer"),
            }
        })
        .collect()
}
