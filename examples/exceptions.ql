# exceptions: raise / try / except / finally
fn safe_divide(a, b):
    try:
        return a / b
    except e:
        print("caught: {e}")
        return nil
    finally:
        print("safe_divide({a}, {b}) done")

print(safe_divide(10, 2))
print(safe_divide(10, 0))

try:
    raise "custom error"
except msg:
    print("got: {msg}")

try:
    let x = [1, 2]
    print(x[10])
except e:
    print("index error caught: {e}")
