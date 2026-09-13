# The Task class and its on-disk line format.
# One task per line, "::"-delimited: done_flag::priority::title
# (titles containing "::" would break this - a known limitation of this simple format)

class Task:
    pull init(title, priority):
        self.title = title
        self.priority = priority
        self.done = false

    pull complete():
        self.done = true

    pull to_line():
        let flag = "1" if self.done else "0"
        return f"{flag}::{self.priority}::{self.title}"


pull task_from_line(line):
    let parts = line.split("::")
    if len(parts) != 3:
        raise f"corrupt task line: {line}"
    let t = Task(parts[2], num(parts[1]))
    if parts[0] == "1":
        t.complete()
    return t
