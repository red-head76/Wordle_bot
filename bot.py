from csv import reader
from itertools import product
from math import log
from random import choice
from tqdm import tqdm


class wordle_game(object):
    """
    Instance of an worlde game

    class attributes:
        top_n (int, default: 5): the amount of words that should be returned
        remaining_words (list of strings): the list of remaining words

    """

    def __init__(self, top_n=5):
        # Number of entries to show
        self.top_n = top_n
        # import wordle word list and set it as remaining words
        with open("./word-list_edit.csv", 'r') as inp:
            self.remaining_words = reader(inp).__next__()  # csv of only one line

        # import top 10 for first guess
        with open("./top10.csv", 'r') as inp:
            self.first_top10 = {rows[0]: float(rows[1]) for rows in reader(inp)}

    def find_best_next_words(self) -> dict:
        """
        Find the top_n words with the most entropy for the remaining words

        Returns:
            top_words (dict): a dictionary of length top_n with key of the word
                        and the entropy value. Highest value is first.

        """
        entropy_dict = {}
        for word in tqdm(self.remaining_words):
            entropy_dict[word] = self.calculate_entropy(word)

        return dict(sorted(entropy_dict.items(), key=lambda x: x[1], reverse=True)[:self.top_n])

    def calculate_entropy(self, word: str) -> float:
        """
        Calculates the entropy for a given word and a list of remaining words

        Args:
            word (string)

        Returns:
            entropy (float)

        """
        entropy = 0
        # For every possible feedback count the amount of remaining words
        # N = nothing right (grey), C = character included (yellow), F = full match (green)
        for combination in product("NCF", repeat=5):
            # number of words in remaining_words matching pattern
            n_words = (len(self.get_matching_words(word, combination)))
            # if n_words = 0 -> p = 0 -> p * log(0) = 0
            if n_words != 0:
                # TODO: this won't yield sum_i p_i = 1, because some words appear twice
                # S' = N * S - N log N, so this measure still works, it's just not the
                # 'real' entropy
                p = n_words / len(self.remaining_words)
                entropy += - p * log(p)

        return entropy

    def get_matching_words(self, input_word: str, combination: str) -> list:
        """
        Returns the list of matching words depending on the input word and the feedback combination
        e.g. the input_word "HOUSE" with combination "NCNFN" means there should be an 'O' somewhere
        and an 'S' on position four. All words matching these conditions are returned in a list.

        Args:
            input_word (string): the input word
            combination (list of strings): The feedback combination
            words (list of strings): The list of words looked up

        Returns:
            matching_words (list)

        """
        matching_words = []
        # Write gray / yellow / green letters into separate lists / dicts
        no_matches = []         # gray letters
        character_matches = {}  # yellow letters
        full_matches = {}       # green letters

        for i in range(5):
            if combination[i] == "N":
                no_matches.append(input_word[i])
            elif combination[i] == "C":
                character_matches[i] = input_word[i]
            elif combination[i] == "F":
                full_matches[i] = input_word[i]
            else:
                raise ValueError(f"'{combination[i]}' is no valid character in combination.")

        # put individual checkers into functions for proper returning to the following word loop
        # If conditions are matched, True is returned

        def check_no_matches(word, matches):
            # Check no matching conditions (grey letters)
            for char in matches:
                # For no_matches:
                # The occurrences cannot be greater than the character or full matches
                if (word.count(char) >
                    list(character_matches.values()).count(char) +
                        list(full_matches.values()).count(char)):
                    return False
            return True

        def check_character_matches(word, matches):
            # Check character included conditions (yellow letters)
            for pos, char in matches.items():
                # For character_matches:
                # The occurrences cannot be smaller than the character or full matches
                if (word.count(char) <
                    list(character_matches.values()).count(char) +
                        list(full_matches.values()).count(char)):
                    return False
                # Check, if its on the same position. Otherwise it would be green
                if word[pos] == char:
                    return False
            return True

        def check_full_matches(word, matches):
            # Check full match conditions (green letters)
            for pos, char in full_matches.items():
                if not word[pos] == char:
                    return False
            return True

        for word in self.remaining_words:
            # ordered from fastest check to slowest
            if check_full_matches(word, full_matches):
                if check_character_matches(word, character_matches):
                    if check_no_matches(word, no_matches):
                        matching_words.append(word)

        return matching_words

    def calc_combination(input_word: str, solution: str) -> str:
        """
        Only necessary for games with bot, where the bot knows the answer
        Returns the combination according to the last input and the solution, e.g.
        input: "TUNER", solution: "REGEN" would return "NNCFC"
        Args:
            input_word: string (string): the last input word
            solution: string (string): the solution

        Returns:
            combination (string)

        """
        combination = list("NNNNN")
        # First set all correct chars to 'F'
        for i in range(5):
            if input_word[i] == solution[i]:
                combination[i] = 'F'
        # Than the character matches to 'C'
        for i in range(5):
            char = input_word[i]
            if char in solution:
                # count occurrences of that char, that are already marked
                already_marked = [n for n in range(5)
                                  if (combination[n] == 'F' or combination[n] == 'C')
                                  and input_word[n] == char]
                # If there are unmarked chars of this type left
                if solution.count(char) - len(already_marked) > 0:
                    combination[i] = 'C'
        # The rest is not matching ('N')
        return "".join(combination)

    def main(self):
        """
        Play wordle with help of the bot

        Args:
            top_n (int, default 5): the amount of suggestions the bot should print
        """
        solution = choice(self.remaining_words)  # choose a random word as solution
        solved = False
        last_input = ""
        print("New game")
        while not solved:
            # if len(self.remaining_words) == 8241:  # if this is the first query
            #     top_words = self.first_top10
            # else:
            top_words = self.find_best_next_words()
            print("Top words to choose:")
            it = iter(top_words)
            for i in range(min(self.top_n, len(self.remaining_words))):
                key = next(it)
                print(key, f"{top_words[key]:.2f}")
            last_input = input("Input your chosen word:").upper()
            combination = wordle_game.calc_combination(last_input, solution)
            # combination = input("Combination:")
            if last_input == solution:
                # if combination == "FFFFF":
                print("Correct!")
                solved = True
            else:
                self.remaining_words = self.get_matching_words(last_input, combination)
            print(len(self.remaining_words))
            if len(self.remaining_words) < 20:
                print("Remaining :\n", self.remaining_words)


if __name__ == '__main__':
    game = wordle_game(top_n=5)
    game.main()
