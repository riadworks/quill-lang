# A password generator with a sha256 "fingerprint" you can safely write down
# to verify you typed the password correctly later, without exposing it.

let LOWER = "abcdefghijklmnopqrstuvwxyz"
let UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
let DIGITS = "0123456789"
let SYMBOLS = "!@#$%^&*-_=+?"

pull ask_int(prompt, default):
    let raw = input(prompt).trim()
    if raw == "":
        return default
    try:
        return num(raw)
    except e:
        print(f"  ({raw} isn't a number, using {default})")
        return default

pull ask_yes_no(prompt, default):
    let raw = input(prompt).trim().lower()
    if raw == "":
        return default
    return raw == "y" or raw == "yes"

pull build_pool(use_upper, use_digits, use_symbols):
    let pool = LOWER
    if use_upper:
        pool += UPPER
    if use_digits:
        pool += DIGITS
    if use_symbols:
        pool += SYMBOLS
    return pool

pull generate(length, pool):
    let chars = []
    let i = 0
    while i < length:
        chars.push(pool[random_int(0, len(pool) - 1)])
        i += 1
    return chars.join("")

pull strength_label(length, pool_size):
    let combinations = pool_size ** length
    if combinations < 1000000:
        return "weak - too short or too small a character set"
    elif combinations < 1000000000000000:
        return "okay"
    else:
        return "strong"

pull main():
    print("=== Quill Password Generator ===")
    let again = true
    while again:
        let length = ask_int("Length (default 16): ", 16)
        let use_upper = ask_yes_no("Include uppercase? (Y/n): ", true)
        let use_digits = ask_yes_no("Include digits? (Y/n): ", true)
        let use_symbols = ask_yes_no("Include symbols? (Y/n): ", true)

        let pool = build_pool(use_upper, use_digits, use_symbols)
        let password = generate(length, pool)

        print("")
        print(f"Password: {password}")
        print(f"Strength: {strength_label(length, len(pool))}")
        print(f"SHA-256 fingerprint (safe to save for later verification): {sha256(password)}")
        print("")

        again = ask_yes_no("Generate another? (y/N): ", false)
    print("Done.")

main()
