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
