import "world.ql" as world_mod

pull main():
    print("=== The Moonlit Tower ===")
    print("Commands: look, go <direction>, take <item>, inventory, quit")
    print("")

    let current = world_mod.build_world()
    let inventory = []
    let playing = true

    while playing:
        print(current.describe())
        let raw = input("> ").trim().lower()
        let parts = raw.split(" ")
        let cmd = parts[0]

        try:
            if cmd == "look":
                pass_noop()
            elif cmd == "go":
                let direction = parts[1]
                if not has(current.exits, direction):
                    print("You can't go that way.")
                elif has(current.locked_exits, direction):
                    let needed = current.locked_exits[direction]
                    let carrying = len([i for i in inventory if i.name == needed]) > 0
                    if carrying:
                        print(f"You unlock the way with the {needed}.")
                        current = current.exits[direction]
                    else:
                        print(f"That way is locked. You need: {needed}")
                else:
                    current = current.exits[direction]
            elif cmd == "take":
                let item_name = slice(parts, 1, len(parts)).join(" ")
                let item = current.find_item(item_name)
                if item == nil:
                    print(f"There's no {item_name} here.")
                else:
                    inventory.push(item)
                    current.remove_item(item_name)
                    print(f"You take the {item_name}.")
                    if item_name == "silver amulet":
                        print("")
                        print("The amulet grows warm. The tower's presence fades around you.")
                        print("You win!")
                        playing = false
            elif cmd == "inventory":
                if len(inventory) == 0:
                    print("You're carrying nothing.")
                else:
                    let names = [i.name for i in inventory]
                    print(f"Carrying: {names.join(", ")}")
            elif cmd == "quit":
                playing = false
                print("Goodbye.")
            else:
                print("I don't understand that.")
        except e:
            print(f"Error: {e}")
        print("")

pull pass_noop():
    return nil

main()
