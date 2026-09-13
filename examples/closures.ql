# closures: a function can capture and mutate a variable from its enclosing scope
fn make_counter():
    let count = 0
    fn increment():
        count = count + 1
        return count
    return increment

let counter = make_counter()
print(counter())
print(counter())
print(counter())

let other = make_counter()
print(other())
