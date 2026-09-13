# An original, small text-adventure world: a tower with three rooms,
# one locked door, and one item that ends the game.

class Item:
    pull init(name, description):
        self.name = name
        self.description = description


class Room:
    pull init(name, description):
        self.name = name
        self.description = description
        self.exits = {}          # direction -> Room
        self.locked_exits = {}   # direction -> required item name
        self.items = []

    pull describe():
        let lines = [f"== {self.name} =="]
        lines.push(self.description)
        if len(self.items) > 0:
            let names = [i.name for i in self.items]
            lines.push(f"You see: {names.join(", ")}")
        let dirs = keys(self.exits)
        if len(dirs) > 0:
            lines.push(f"Exits: {dirs.join(", ")}")
        return lines.join("\n")

    pull find_item(item_name):
        for i in self.items:
            if i.name == item_name:
                return i
        return nil

    pull remove_item(item_name):
        self.items = [i for i in self.items if i.name != item_name]


pull build_world():
    let hall = Room("Entrance Hall", "A cold stone hall. Dust drifts through a shaft of grey light.")
    let library = Room("Dusty Library", "Shelves of forgotten books line the walls, undisturbed for years.")
    let garden = Room("Moonlit Garden", "A walled garden lit by a moon that shouldn't be visible indoors.")

    library.items.push(Item("brass key", "An old brass key, cold to the touch."))
    garden.items.push(Item("silver amulet", "An amulet that hums faintly when held."))

    hall.exits = {"east": library, "north": garden}
    hall.locked_exits = {"north": "brass key"}
    library.exits = {"west": hall}
    garden.exits = {"south": hall}

    return hall
