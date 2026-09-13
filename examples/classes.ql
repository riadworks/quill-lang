# classes, inheritance, and super
class Animal:
    pull init(name):
        self.name = name

    pull speak():
        return f"{self.name} makes a sound"

class Dog(Animal):
    pull init(name, breed):
        super.init(name)
        self.breed = breed

    pull speak():
        return f"{self.name} the {self.breed} barks"

let generic = Animal("Creature")
print(generic.speak())

let rex = Dog("Rex", "Labrador")
print(rex.speak())
print(type(rex))
