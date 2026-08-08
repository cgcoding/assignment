#[derive(Debug)]
struct Roster {
    names: Vec<String>,
    log: Vec<String>,
}

fn longest(roster: &Roster) -> usize {
    roster
        .names
        .iter()
        .enumerate()
        .max_by_key(|(_, name)| name.len())
        .map(|(index, _)| index)
        .unwrap()
}

fn add_name(roster: &mut Roster, name: String) {
    let previous = longest(roster);

    roster.log.push(format!(
        "Previous longest name: {}",
        roster.names[previous]
    ));

    roster.names.push(name);

    println!("Previous longest name was {}", roster.names[previous]);
}

pub fn main() {
    let mut roster = Roster {
        names: vec![
            String::from("Mira"),
            String::from("Aniruddha"),
        ],
        log: Vec::new(),
    };

    add_name(&mut roster, String::from("Christopher"));
    println!("{roster:?}");
}
