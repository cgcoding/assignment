trait Scored {
    fn score(&self) -> i32;
}
struct Student {
    name: String,
    mark: i32,
}
impl Scored for Student {
    fn score(&self) -> i32 {
        self.mark
    }
}

fn best_by<T, F>(items: &[T], mut score: F) -> Option<&T>
where
    T: Scored,
    F: FnMut(&T) -> i32,
{
    let mut best = items.first()?;
    let mut best_score = score(best);

    for item in &items[1..] {
        let item_score = score(item);

        if item_score > best_score {
            best = item;
            best_score = item_score;
        }
    }

    Some(best)
}

fn main() {
    let students = vec![
        Student { name: "Mira".into(), mark: 72 },
        Student { name: "Ravi".into(), mark: 84 },
        Student { name: "Anu".into(), mark: 79 },
    ];
    let mut calls = 0;
    let winner = best_by(&students, |student| {
        calls += 1;
        student.score()
    })
    .unwrap();
    println!(
        "{} scored {}; scoring function called {} times",
        winner.name, winner.mark, calls
    );
}
