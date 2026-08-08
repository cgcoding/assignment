pub(crate) fn passed(score: u32) -> bool {
    score >= 40
}

pub(crate) fn earned_distinction(score: u32) -> bool {
    score >= 75
}
