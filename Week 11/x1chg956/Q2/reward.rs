#[derive(Debug)]
struct Student {
    name: String,
    marks: Vec<i32>,
}

fn reward(student: &mut Student, add_marks: i32) -> i32 {
    let name = &student.name;
    let top = student.marks.iter_mut().max().unwrap();

    println!("Rewarding {name}; old highest mark = {top}");
    *top += 5;
    let top = *top;
    student.marks.push(add_marks);

    println!("Updated student: {student:?}");
    top
}

fn main() {
    let mut s = Student {
        name: String::from("Priyanka"),
        marks: vec![72, 81, 76],
    };
    let additional_marks = 75;
    let rewarded_mark = reward(&mut s, additional_marks);
    println!("{s:?}; rewarded mark = {rewarded_mark}");
}
