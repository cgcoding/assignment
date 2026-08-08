use crate::model::StudentRecord;

pub(crate) fn rank_records(mut records: Vec<StudentRecord>) -> Vec<StudentRecord> {
    records.sort_by(|left, right| {
        right
            .score
            .cmp(&left.score)
            .then_with(|| left.name.cmp(&right.name))
    });

    records
}
