#/backend/test_scoring.py

import unittest
from app import calculate_score

class TestScoring(unittest.TestCase):
    def test_blackjack(self)
        hand = [{'rank': 'A', 'suit': '♠'}, {'rank': 'K', 'suit': '♥'}]
        self.assertEqual(calculate_score(hand), 21)

    def test_multiple_aces(self):
        hand = [{'rank': 'A', 'suit': '♠'}, {'rank': 'A', 'suit': '♦'}, {'rank': '9', 'suit': '♥'}]
        self.assertEqual(calculate_score(hand), 21)

    def test_bust(self):
        hand = [{'rank': '10', 'suit': '♠'}, {'rank': '9', 'suit': '♦'}, {'rank': '5', 'suit': '♥'}]
        self.assertEqual(calculate_score(hand), 24)

if __name__ == '__main__':
    unittest.main()