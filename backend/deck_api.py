import requests

class DeckAPI:
    BASE_URL = "https://deckofcardsapi.com/api/deck"

    def __init__(self):
        self.deck_id = None

    def new_deck(self):
        response = requests.get(f"{self.BASE_URL}/new/shuffle/?deck_count=1")
        data = response.json()
        self.deck_id = data["deck_id"]
        return self.deck_id

    def draw_cards(self, count=1):
        if not self.deck_id:
            raise ValueError("Deck ID not initialized.")
        url = f"{self.BASE_URL}/{self.deck_id}/draw/?count={count}"
        response = requests.get(url)
        cards = response.json()["cards"]
        return [self._sanitize_card(c) for c in cards]

    def _sanitize_card(self, card):
        rank_map = {
            "ACE": "A", "2": "2", "3": "3", "4": "4", "5": "5",
            "6": "6", "7": "7", "8": "8", "9": "9", "10": "10",
            "JACK": "J", "QUEEN": "Q", "KING": "K"
        }

        return {
            "suit": card["suit"][0],  # 'HEARTS' → 'H'
            "rank": rank_map.get(card["value"], card["value"]),
            "image": card["image"]
        }
