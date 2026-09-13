# lists and maps
let nums = [5, 3, 8, 1, 9]
push(nums, 2)
print("nums: {nums}")
print("sorted: {sorted(nums)}")
print("sum: {sum(nums)}, max: {max(nums)}, min: {min(nums)}")

let doubled = []
for n in nums:
    push(doubled, n * 2)
print("doubled: {doubled}")

let person = {"name": "Ada", "age": 36}
print("{person["name"]} is {person["age"]}")
for key in keys(person):
    print("{key} => {person[key]}")
