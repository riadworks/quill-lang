# classes, inheritance, and super
class Animal:
    fn init(name):
        self.name = name

    fn speak():
        return "{self.name} makes a sound"

class Dog(Animal):
    fn init(name, breed):
        super.init(name)
        self.breed = breed

    fn speak():
        return "{self.name} the {self.breed} barks"

let generic = Animal("Creature")
print(generic.speak())

let rex = Dog("Rex", "Labrador")
print(rex.speak())
print(type(rex))
