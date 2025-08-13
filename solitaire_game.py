import random
import sys

# Constants for the suits and ranks
SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# Card class to represent each card
class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f'{self.rank} of {self.suit}'

# Deck class to represent a deck of cards
class Deck:
    def __init__(self):
        self.cards = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        random.shuffle(self.cards)

    def draw_card(self):
        return self.cards.pop() if self.cards else None

# Solitaire game class
class Solitaire:
    def __init__(self):
        self.deck = Deck()
        self.tableau = [[] for _ in range(7)]
        self.foundation = {suit: [] for suit in SUITS}
        self.stock = []
        self.waste = []
        self.setup_game()

    def setup_game(self):
        # Deal cards to the tableau
        for i in range(7):
            for j in range(i, 7):
                self.tableau[j].append(self.deck.draw_card())

    def play(self):
        print("Welcome to Solitaire!")
        self.print_tableau()

    def print_tableau(self):
        print("Tableau:")
        for i, pile in enumerate(self.tableau):
            print(f'Pile {i + 1}:', ' '.join(str(card) for card in pile))

# Main function to start the game
def main():
    game = Solitaire()
    game.play()

if __name__ == '__main__':
    main()
