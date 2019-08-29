import random
import subprocess
import os
import re
import time
import sys

GUESS_REGEX = r"in (.*) guesses"
QUALITY_REGEX = r"Approximate quality = (.*)%"
ACCURACY = 2
TESTS = 5
CARD_COUNT = 4
SEED = 1337
TIMEOUT = 30  # Timeout in seconds
random.seed(SEED)


def randomCard():
    """Returns a random playing card

    Returns:
        [String] -- [Random playing card]
    """
    suitchars = "CDHS"
    rankchars = "23456789TJQKA"
    return random.choice(rankchars) + random.choice(suitchars)


def randomCardList(cardCount):
    """Returns a list of random, unique playing cards

    Arguments:
        cardCount {int} -- [The number of cards to generate]

    Returns:
        [[String]] -- [List of unique, randomly generated cards]
    """
    cards = []
    while True:
        card = randomCard()
        if (not card in cards):
            cards.append(card)
        if len(cards) == cardCount:
            return cards


def runGuess(level):
    """Executes Proj1Test at a specific 'level'. 'level' being the size of card 
    input

    Arguments:
        level {int} -- Number of input cards 

    Returns:
        [([String], float, float, float, float)] -- Tuple containing the 
        following information (in order) about the run:
            [0] - The cards used
            [1] - The number of guesses made
            [2] - The quality
            [3] - The time taken to execute
    """
    cards = randomCardList(level)
    timeStarted = time.time()
    output = subprocess.getoutput(["Proj1Test.exe"] + cards)
    timeDelta = round(time.time() - timeStarted, ACCURACY)
    guesses = round(float(re.findall(GUESS_REGEX, output)[0]), ACCURACY)
    quality = round(float(re.findall(QUALITY_REGEX, output)[0]), ACCURACY)
    return (cards, guesses, quality, timeDelta)


def mean(numbers):
    # Returns the arithmetic mean
    return float(sum(numbers)) / max(len(numbers), 1)


results = []
for i in range(TESTS):
    result = runGuess(CARD_COUNT)
    results.append(result)
    average_guesses = round(mean([x[1] for x in results]), ACCURACY)
    average_quality = round(mean([x[2] for x in results]), ACCURACY)
    max_time = max([x[3] for x in results])
    max_guesses = max([x[1] for x in results])
    min_guesses = min([x[1] for x in results])
    min_quality = min([x[2] for x in results])
    print("Total Runs: " + str(i) + " |  " + str(result) + "\nAverage Guesses: " + str(average_guesses) +
          "\tAverage Quality: " + str(average_quality) +
          "\tMax Time: " + str(max_time) +
          "\tMax Guesses: " + str(max_guesses) +
          "\tMin Guesses: " + str(min_guesses) +
          "\tMin Quality: " + str(min_quality)
          )

total_time = round(sum([x[3] for x in results]), ACCURACY)
print("Completed in " + str(total_time) + " seconds")
