# dot-method syntax on built-in types, ternary, augmented assignment, new operators
let s = "  Hello World  "
print(s.trim())
print(s.trim().upper())
print(s.trim().lower().split(" "))
print("py-lang".replace("py", "quill"))
print("abc".repeat(3))
print("hello".starts_with("he"))

let nums = [5, 3, 8, 1]
nums.push(9)
print(nums)
print(nums.contains(8))
print(nums.index_of(8))
print(nums.sort())
print(nums.map(fn(x): return x * x))
print(nums.filter(fn(x): return x > 4))
print(nums.reduce(fn(acc, x): return acc + x, 0))
print([1, 2, 3].join("-"))

let m = {"a": 1}
print(m.get("a"))
print(m.get("missing", "default"))
print(m.has("a"))

let x = 7
print("big" if x > 5 else "small")

let counter = 0
counter += 5
counter *= 2
print(counter)

print(7 // 2)
print(sqrt(16))
print(floor(3.7))
print(ceil(3.2))
print(PI)
