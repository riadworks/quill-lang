# lists and maps
let nums = [5, 3, 8, 1, 9]
push(nums, 2)
print(f"nums: {nums}")
print(f"sorted: {sorted(nums)}")
print(f"sum: {sum(nums)}, max: {max(nums)}, min: {min(nums)}")

let doubled = []
for n in nums:
    push(doubled, n * 2)
print(f"doubled: {doubled}")

let person = {"name": "Ada", "age": 36}
print(f"{person["name"]} is {person["age"]}")
for key in keys(person):
    print(f"{key} => {person[key]}")
