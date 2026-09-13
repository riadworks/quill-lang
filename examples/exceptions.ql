# exceptions: raise / try / except / finally
pull safe_divide(a, b):
    try:
        return a / b
    except e:
        print(f"caught: {e}")
        return nil
    finally:
        print(f"safe_divide({a}, {b}) done")

print(safe_divide(10, 2))
print(safe_divide(10, 0))

try:
    raise "custom error"
except msg:
    print(f"got: {msg}")

try:
    let x = [1, 2]
    print(x[10])
except e:
    print(f"index error caught: {e}")
