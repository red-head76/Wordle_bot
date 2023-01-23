import bot
import unittest
from csv import reader

# import wordle word list
with open("./word-list_edit.csv", 'r') as inp:
    word_list = reader(inp).__next__()[:20]  # csv of only one line
# ['OESTE', 'TUNER', 'HAREM', 'FUXEN', 'AGENS', 'DOOFE', 'RUFEN', 'FURZT', 'EISIG', 'EUMEL',
# 'WINKT', 'RUPFT', 'DISCO', 'ALKIN', 'OESEN', 'KITTS', 'DIEBS', 'TWETE', 'MOTZT', 'RABES']


class test_bot(unittest.TestCase):

    def test_get_matching_words(self):
        result_1 = bot.get_matching_words("REGEN", "NNNNN", word_list)
        desired_result_1 = ["DISCO", "KITTS", "MOTZT"]
        self.assertListEqual(result_1, desired_result_1)

        result_2 = bot.get_matching_words("REGEN", "CNNFC", word_list)
        desired_result_2 = ["TUNER"]
        self.assertListEqual(result_2, desired_result_2)

        result_3 = bot.get_matching_words("REGEN", "FNNNN", word_list)
        desired_result_3 = ["RUPFT"]
        self.assertListEqual(result_3, desired_result_3)

        result_4 = bot.get_matching_words("SENSE", "NCCNN", word_list)
        desired_result_4 = ["FUXEN", "RUFEN"]
        self.assertListEqual(result_4, desired_result_4, word_list)
