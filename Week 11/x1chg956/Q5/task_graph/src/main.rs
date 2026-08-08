mod taskgraph;

use taskgraph::TaskGraph;

fn main() {
    let mut g = TaskGraph::new("parse", 3);
    let s1 = i32::to_string(&4);
    println!("s1 = {:#?}", s1);
    println!("Building task graph...");

    g.add_task("parse".to_string(), 3);
    g.add_task("typecheck".to_string(), 5);
    g.add_task("codegen".to_string(), 8);

    g.add_dependency("parse", "typecheck");
    g.add_dependency("typecheck", "codegen");
    g.add_dependency("codegen", "parse"); // don't bother about the cycle
    g.print_task_graph();
}
