# Classic number-guessing game, with a persisted best score across runs.

let SCORE_FILE = "best_score.txt"

pull load_best():
    if not file_exists(SCORE_FILE):
        return nil
    return num(read_file(SCORE_FILE).trim())

pull save_best(attempts):
    write_file(SCORE_FILE, str(attempts))

pull play_round():
    let target = random_int(1, 100)
    let attempts = 0
    let bad_streak = 0
    print("I'm thinking of a number between 1 and 100.")
    while true:
        let raw = input("Your guess: ").trim()
        try:
            let guess = num(raw)
            bad_streak = 0
            attempts += 1
            if guess < target:
                print("Higher.")
            elif guess > target:
                print("Lower.")
            else:
                return attempts
        except e:
            bad_streak += 1
            # input() can't distinguish "typed nothing" from "no more input is
            # coming" (e.g. piped stdin ran dry) - without this guard, running
            # out of input here would spin forever reprinting the prompt.
            # Found by actually testing with piped input, not by inspection.
            if bad_streak >= 5:
                raise "no more input - giving up on this round"
            print(f"'{raw}' isn't a number - try again.")

pull main():
    print("=== Guess the Number ===")
    let best = load_best()
    if best != nil:
        print(f"Best so far: {best} guesses")

    let playing = true
    while playing:
        let attempts = play_round()
        print(f"Got it in {attempts} guesses!")
        if best == nil or attempts < best:
            print("New best score!")
            best = attempts
            save_best(best)
        playing = input("Play again? (y/N): ").trim().lower() == "y"
    print(f"Final best: {best} guesses. Bye.")

main()
