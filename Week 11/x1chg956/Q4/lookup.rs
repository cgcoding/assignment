enum Found<'a, 'b> {
    Official(&'a str),
    #[allow(dead_code)]
    Alias(&'b str),
}

fn lookup<'a, 'b>(
    official: &'a [String],
    aliases: &'b [String],
    target: &str,
) -> Option<Found<'a, 'b>> {
    if let Some(name) = official.iter().find(|name| name.as_str() == target) {
        return Some(Found::Official(name.as_str()));
    }

    if let Some(name) = aliases.iter().find(|name| name.as_str() == target) {
        return Some(Found::Alias(name.as_str()));
    }

    None
}

pub fn main() {
    let official = vec![String::from("Mira")];
    let saved;
    {
        let aliases = vec![String::from("Mary")];
        let found = lookup(&official, &aliases, "Mira");
        saved = match found {
            Some(Found::Official(name)) => Some(name),
            Some(Found::Alias(_)) => None,
            None => None,
        };
    }
    match saved {
        Some(name) => println!("Found name {}", name),
        None => println!("Name Mira not found!"),
    }
}
