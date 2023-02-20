from wordfreq import word_frequency, zipf_frequency
import numpy as np
from csv import reader, writer
from itertools import product
from random import choice
from os.path import isfile
from re import findall
from tqdm import tqdm


# Helper functions ############################################################

def edit_word_list():
    with open("./word-list.js", 'r') as inp:
        data = inp.readline()

    # set to avoid duplicates
    words = set(findall(r"(?:')([A-Z]{5})(?:')", data))

    with open("./word-list_edit.csv", 'w') as out:
        writer(out).writerow(words)


def create_pattern_table():
    with open("./word-list_edit.csv", 'r') as inp:
        words = reader(inp).__next__()  # csv of only one line

    # ubyte = 8-bit unsigned int -> from 0 to 255, which is enough for 243 combinations
    pattern_table = np.empty((len(words), len(words)), dtype=np.ubyte)

    for i, word1 in tqdm(enumerate(words)):
        for j, word2 in enumerate(words):
            pattern_table[i, j] = wordle_game.combination_str_to_int(
                wordle_game.calc_combination(word1, word2))

    np.save("pattern_table", pattern_table)


# game class ##################################################################

class wordle_game(object):
    """
    Instance of an worlde game

    class attributes:
        top_n (int, default: 5): the amount of words that should be returned
        first_top10 (dict (string: int)): a dictionary with the first top10 words
        remaining_words (np.array (str)): the list of remaining words
        pattern_table (np.array (ushort)): the pattern table for the remaining_words


    """

    def __init__(self, top_n=5, freq_scaling='linear'):
        # Number of entries to show
        self.top_n = top_n
        # import wordle word list and set it as remaining words
        new_word_list = False
        if not isfile("./word-list_edit.csv"):
            print("Creating new word list...")
            edit_word_list()
            new_word_list = True
        with open("./word-list_edit.csv", 'r') as inp:
            self.remaining_words = np.array(reader(inp).__next__())  # csv of only one line

        if freq_scaling == 'linear':
            self.word_freq = np.array(
                [word_frequency(word, 'de') for word in self.remaining_words])
        elif freq_scaling == 'log':
            self.word_freq = np.array(
                [zipf_frequency(word, 'de') for word in self.remaining_words])
        else:
            raise ValueError(f"{freq_scaling} is not a valid scaling. Choose 'linear' or 'log'")

        # import top 10 for first guess
        with open("./top10.csv", 'r') as inp:
            self.first_top10 = {rows[0]: float(rows[1]) for rows in reader(inp)}

        # import pattern_table
        if not isfile("./pattern_table.npy") or new_word_list:
            print("Creating new pattern table...")
            create_pattern_table()
        self.pattern_table = np.load("./pattern_table.npy")

    def find_best_next_words(self) -> dict:
        """
        Find the top_n words with the most entropy for the remaining words

        Returns:
            top_words (dict): a dictionary of length top_n with key of the word
                        and the entropy value. Highest value is first.

        """
        entropies = [self.calculate_entropy(word) for word in tqdm(self.remaining_words)]
        # sort descending
        sort_mask = np.flip(np.argsort(entropies))
        return dict(zip(np.asarray(self.remaining_words)[sort_mask][:self.top_n],
                        np.asarray(entropies)[sort_mask][:self.top_n]))

    def calculate_entropy(self, word: str) -> float:
        """
        Calculates the entropy for a given word and a list of remaining words

        Args:
            word (string)

        Returns:
            entropy (float)

        """
        w_counts = np.empty(243)
        for pattern in range(243):
            indices_according_to_pattern = np.where(
                self.pattern_table[self.remaining_words == word].ravel() == pattern)[0]
            w_counts[pattern] = np.sum(self.word_freq[indices_according_to_pattern])
        w_counts = w_counts[np.nonzero(w_counts)]
        return np.sum(w_counts * np.log(1 / w_counts), axis=0)

    def get_matching_words(self, input_word: str, combination: str) -> np.array:
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
        # the list of the corresponding patterns with respect to the input word
        patterns = self.pattern_table[self.remaining_words == input_word].ravel()
        # the indices, at which the pattern number equals
        # nonzero returns a tuple, thats why [0]
        return (patterns == wordle_game.combination_str_to_int(combination)).nonzero()[0]

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
                # If its already a full match, don't change it
                if input_word[i] == solution[i]:
                    continue
                # Count occurrences of that char, that are already marked
                already_marked = [n for n in range(5)
                                  if (combination[n] == 'F' or combination[n] == 'C')
                                  and input_word[n] == char]
                # If there are unmarked chars of this type left
                if solution.count(char) - len(already_marked) > 0:
                    combination[i] = 'C'
        # The rest is not matching ('N')
        return "".join(combination)

    def combination_str_to_int(combination: str) -> int:
        """
        Convert a string representation of a combination to an integer.
        The rule for that is the order in which the combinations appear with the 'product'-function

        Args:
            combination (string): the combination in string representation  (e.g. "NNNFC")

        Returns:
            combination_as_int (integer)
        """
        return list(product("NCF", repeat=5)).index(tuple(combination))

    def combination_int_to_str(combination_int: int) -> str:
        """
        Convert a integer representation of a combination to an string.
        The rule for that is the order in which the combinations appear with the 'product'-function

        Args:
            combination (int): the combination in string representation (from 0 to 242)

        Returns:
            combination (string)
        """
        return "".join(list(product("NCF", repeat=5))[combination_int])

    def main(self):
        """
        Play wordle with help of the bot

        Args:
            top_n (int, default 5): the amount of suggestions the bot should print
        """
        solution = choice(self.remaining_words)  # choose a random word as solution
        solved = False
        print("New game")
        while not solved:
            top_words = self.find_best_next_words()
            print("Top words to choose:")
            it = iter(top_words)
            for i in range(min(self.top_n, len(self.remaining_words))):
                key = next(it)
                print(key, f"{top_words[key]:.2f}")
            last_input = ""
            matching_words = np.array([])
            last_input = input("Input your word:").upper()
            while not matching_words.size:  # while there are no matching words (strict mode)
                while (not len(last_input) == 5):  # while the last input is not 5 chars long
                    last_input = input("Word needs to be 5 letters long. New word:").upper()
                combination = wordle_game.calc_combination(last_input, solution)
                matching_words = self.get_matching_words(last_input, combination)
                if not matching_words.size:
                    last_input = input("Word not in remaining word list. New word:").upper()

            # reduce remaining_words and pattern table according to matching_words
            self.remaining_words = self.remaining_words[matching_words]
            self.pattern_table = self.pattern_table[np.ix_(matching_words, matching_words)]
            if last_input == solution:
                # if combination == "FFFFF":
                print("Correct!")
                solved = True
            else:
                print(f"{len(self.remaining_words)} words left")
                if len(self.remaining_words) < 20:
                    print("Remaining :\n", self.remaining_words)


if __name__ == '__main__':
    game = wordle_game(top_n=5)
    game.main()
