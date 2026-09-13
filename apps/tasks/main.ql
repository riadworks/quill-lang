import "task.ql" as task_mod

let SAVE_FILE = "tasks.txt"

pull load_tasks():
    let tasks = []
    if not file_exists(SAVE_FILE):
        return tasks
    let content = read_file(SAVE_FILE)
    for line in content.split("\n"):
        if line.trim() != "":
            tasks.push(task_mod.task_from_line(line))
    return tasks

pull save_tasks(tasks):
    let lines = []
    for t in tasks:
        lines.push(t.to_line())
    write_file(SAVE_FILE, lines.join("\n"))

pull print_tasks(tasks):
    if len(tasks) == 0:
        print("  (no tasks yet)")
        return
    let i = 0
    while i < len(tasks):
        print(f"  {i + 1}. {tasks[i].to_string()}")
        i += 1

pull print_menu():
    print("")
    print("=== Quill Tasks ===")
    print("1) List tasks")
    print("2) Add task")
    print("3) Complete task")
    print("4) Remove task")
    print("5) Quit")

pull ask_index(tasks, prompt):
    let raw = input(prompt).trim()
    let idx = num(raw) - 1
    if idx < 0 or idx >= len(tasks):
        raise f"no task numbered {raw}"
    return idx

pull main():
    let tasks = load_tasks()
    let running = true
    while running:
        print_menu()
        let choice = input("> ").trim()
        try:
            if choice == "1":
                print_tasks(tasks)
            elif choice == "2":
                let title = input("Title: ").trim()
                let priority = num(input("Priority (1-5): ").trim())
                tasks.push(task_mod.Task(title, priority))
                save_tasks(tasks)
                print("Added.")
            elif choice == "3":
                print_tasks(tasks)
                let idx = ask_index(tasks, "Complete which #: ")
                tasks[idx].complete()
                save_tasks(tasks)
                print("Marked complete.")
            elif choice == "4":
                print_tasks(tasks)
                let idx = ask_index(tasks, "Remove which #: ")
                let removed = tasks.pop(idx)
                save_tasks(tasks)
                print(f"Removed '{removed.title}'.")
            elif choice == "5":
                running = false
                print("Bye.")
            else:
                print(f"Not a valid choice: {choice}")
        except e:
            print(f"Error: {e}")

main()
