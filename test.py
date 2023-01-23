import bot
import unittest


class test_bot(unittest.TestCase):

    def test_get_matching_words(self):
        game = bot.wordle_game()
        game.remaining_words = game.remaining_words[:20]
        # ['OESTE', 'TUNER', 'HAREM', 'FUXEN', 'AGENS', 'DOOFE', 'RUFEN', 'FURZT', 'EISIG',
        # 'EUMEL', 'WINKT', 'RUPFT', 'DISCO', 'ALKIN', 'OESEN', 'KITTS', 'DIEBS', 'TWETE', 'MOTZT',
        # 'RABES']

        result_1 = game.get_matching_words("REGEN", "NNNNN")
        desired_result_1 = ["DISCO", "KITTS", "MOTZT"]
        self.assertListEqual(result_1, desired_result_1)

        result_2 = game.get_matching_words("REGEN", "CNNFC")
        desired_result_2 = ["TUNER"]
        self.assertListEqual(result_2, desired_result_2)

        result_3 = game.get_matching_words("REGEN", "FNNNN")
        desired_result_3 = ["RUPFT"]
        self.assertListEqual(result_3, desired_result_3)

        result_4 = game.get_matching_words("SENSE", "NCCNN")
        desired_result_4 = ["FUXEN", "RUFEN"]
        self.assertListEqual(result_4, desired_result_4)
