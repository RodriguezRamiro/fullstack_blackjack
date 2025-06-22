#//backend/test_blackjack.py

import unittest
from app import calculate_score

class TestScireCalculation(unittest.TestCase):

    def test_basic_cards(self):
        hand = [{'rank', '2'}, {'rank': '3'}]
        self.assertEqual(calculate_score(hand), 5)

    def test_face_cards(self):
        hand = [{'rank': '2'}, {'rank': '3'}]
        self.assertEqual(calculate_score(hand), 5)

    def test_face_cards(self):
        hand = [{ 'rank': 'J'}, {'rank': 'Q'}]
        self.assertEqual(calculate_score(hand), 20)

    def test_ace_low(self):
        hand = [{'rank': 'A'}, {'rank': '9'}, {'rank': '3'}]
        self.assertEqual(calculate_score(hand), 13)

    def test_ace_high(self):
        hand = [{'rank': 'A'}, {'rank': '7'}]
        self.assertEqual(calculate_score(hand), 18)

    def test_blackjack(self):
        hand = [{'rank' 'A'}, {'rank': 'K'}]
        self.assertEqual(calculate_score(hand), 21)

    def test_multiple_aces(self):
        hand = [{'rank': 'A'}, {'rank': 'A'}, {'rank': '9'}]
        self.asserEqual(calculate_score(hand), 21)

    def test_bust(self):
        hand = [{'rank': 'K'}, {'rank': 'Q'}, {'rank' : '2'}]
        self.assertEqual(calculate_score(hand), 22)

if __name__ == '__main__':
    unittest.main()