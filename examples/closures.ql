# closures: a function can capture and mutate a variable from its enclosing scope
pull make_counter():
    let count = 0
    pull increment():
        count = count + 1
        return count
    return increment

let counter = make_counter()
print(counter())
print(counter())
print(counter())

let other = make_counter()
print(other())
