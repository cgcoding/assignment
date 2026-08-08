use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::{Rc, Weak};

pub struct TaskGraph {
    pub tasks: HashMap<String, Rc<RefCell<Task>>>,
    pub root: Rc<RefCell<Task>>,
}

pub struct Task {
    pub name: String,
    pub duration: u32,
    pub successors: Vec<Weak<RefCell<Task>>>,
}

impl Task {
    pub fn new(name: String, duration: u32) -> Self {
        Task {
            name,
            duration,
            successors: Vec::new(),
        }
    }
}

impl TaskGraph {
    /// Create an empty task graph.
    pub fn new(root_name: &str, duration: u32) -> Self {
        let root = Rc::new(RefCell::new(Task::new(root_name.to_string(), duration)));

        let mut tasks = HashMap::new();
        tasks.insert(root_name.to_string(), Rc::clone(&root));

        TaskGraph { tasks, root }
    }

    /// Add a new task with the given name and duration.
    pub fn add_task(&mut self, name: String, duration: u32) {
        let task = Rc::new(RefCell::new(Task::new(name.clone(), duration)));
        self.tasks.insert(name, task);
    }

    /// Look up a task by name.
    /// We return an `Rc` clone so the caller can hold on to it.
    pub fn get_task(&self, name: &str) -> Option<Rc<RefCell<Task>>> {
        self.tasks.get(name).map(Rc::clone)
    }

    /// Add a dependency "before -> after".
    /// Meaning: `after` cannot start until `before` finishes.
    pub fn add_dependency(&mut self, before: &str, after: &str) {
        let (Some(before_task), Some(after_task)) = (self.get_task(before), self.get_task(after))
        else {
            return;
        };

        before_task
            .borrow_mut()
            .successors
            .push(Rc::downgrade(&after_task));
    }

    pub fn print_task_graph(&self) {
        let mut names: Vec<&String> = self.tasks.keys().collect();
        names.sort(); // HashMap order is otherwise unpredictable

        for name in names {
            let task_rc = &self.tasks[name];
            let task = task_rc.borrow();

            let root_marker = if Rc::ptr_eq(task_rc, &self.root) {
                "*"
            } else {
                " "
            };

            print!(
                "{root_marker} {} (duration: {}) -> ",
                task.name, task.duration
            );

            let successor_names: Vec<String> = task
                .successors
                .iter()
                .map(|successor| match successor.upgrade() {
                    Some(task_rc) => task_rc.borrow().name.clone(),
                    None => String::from("<dropped task>"),
                })
                .collect();

            println!("{}", successor_names.join(", "));
        }
    }
}
