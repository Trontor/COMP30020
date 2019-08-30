"""
:name: test.py
:author: Rohyl Joshi, Callum Holmes
:purpose: Testing of Project 1 executables for performance with 
          randomised card selection and data collation.
"""

from pandas import DataFrame
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
TIMEOUT = 10

DISPLAY_HEADER = "Total Runs: {0} | {1}"
DISPLAY_DATA = "Guesses: Min {0} -- Avg {1:.2f} -- Max {2}   ||   Max Time {3:.2f}   ||   Quality : Min {4:.2f} -- Avg {5:.2f}"
ROHYL_DISPLAY_DATA = "Average Guesses: {1:.2f} Average Quality: {4:.2f} Max Time: {3:.2f} Max Guesses: {2} Min Guesses: {0} Min Quality: {4:.2f}"


class Logger:
    """
    A containment for entering and extracting
    data relevant to analysis and debugging.

    Functions:
        logError -- For storing data pertaining to failed tests
        logSuccess -- For storing data from successful tests
        summarise -- For collating and displaying test data
        finalOutput -- Any final data displays desired 
    """

    def __init__(self):
        # ["Answer", "cardCount", "Guesses", "Quality", "TimeTaken"]
        self.data = list()
        self.erroneousInputs = list()

    def logError(self, cardInput):
        """Store the data for an error that has occurred."""
        self.erroneousInputs.append(cardInput)
    
    def logSuccess(self, cardInput, guessCount, guessQuality, guessTime): 
        """Append data of a successful test to the dataframe."""
        self.data.append([cardInput, len(cardInput), guessCount, guessQuality, guessTime])
    
    def summarise(self, data=None):
        """Calculates and displays desired fields to summarise data.

        Arguments:
            data [abstract] -- Will be printed if passed, e.g. the actual card state        
        """

        df = DataFrame(self.data, columns=["Answer", "cardCount", "Guesses", "Quality", "TimeTaken"])
        numericData = df[["Guesses", "Quality", "TimeTaken"]]
        totalRuns = len(df)        
        averageGuess, averageQuality = numericData.agg(mean)[["Guesses", "Quality"]]
        maxTime, maxGuess = numericData.max()[["TimeTaken", "Guesses"]]
        minGuess, minQuality = numericData.min()[["Guesses", "Quality"]]

        # Display data
        print(DISPLAY_HEADER.format(totalRuns, (data if not None else "")))
        print(ROHYL_DISPLAY_DATA.format(minGuess, averageGuess, maxGuess, maxTime, minQuality, averageQuality))
    
    def finalOutput(self):
        totalTime = sum(map(lambda x : x[4], self.data))
        print(f"Completed in {totalTime:.2f} seconds.")
        
        if len(self.erroneousInputs) > 0:
            print("Answers that were failed: ")
            for answer in self.erroneousInputs:
                print(answer)
        else:
            print("No errors were encountered!")

def cardSpace():
    """Generates all possible cards in a standard deck of 52 cards.

    Returns: [String] - the deck of cards in str representation.
    
    """
    suitchars = "CDHS"
    rankchars = "23456789TJQKA"
    return [x+y for x in rankchars for y in suitchars]

def randomCardList(cardCount):
    """Returns a list of random, unique playing cards"""
    return random.sample(cardSpace(), k=cardCount)

def runGuess(answer, logger, display=True):
    """Executes Proj1Test for a given guess.

    Arguments:
        guess {[String]} -- list of input cards forming the guess
        logger {Logger} -- The handler for storing the run's data
        display {Boolean=True} -- Controls whether results are printed.

    Returns:
        [([String], float, float, float, float)] -- Tuple containing the 
        following information (in order) about the run:
            [0] - The cards used
            [1] - The number of guesses made
            [2] - The quality
            [3] - The time taken to execute
    """
    timeStarted = time.time()
    args = ["Proj1Test.exe"] + answer
    try:
        timeDelta = round(time.time() - timeStarted, ACCURACY)
        output = subprocess.check_output(args, timeout=TIMEOUT).decode('utf-8')
        guesses = round(float(re.findall(GUESS_REGEX, output)[0]), ACCURACY)
        quality = round(float(re.findall(QUALITY_REGEX, output)[0]), ACCURACY)
        data = (answer, guesses, quality, timeDelta)
        logger.logSuccess(*data)
        # Summary so far
        if display:
            logger.summarise(data)
    except subprocess.TimeoutExpired:
        if display:
            print(
                f">> TIMEOUT ({TIMEOUT}s) OCCURRED WITH {answer}. Continuing with analysis\n")
        # TODO: note that this input timed out
        logger.logError(answer)
    except IndexError:
        # The program did not execute successfully.
        if display:
            print(
                f">> ERROR OCCURRED WITH {answer}. Continuing with analysis\n")
        logger.logError(answer)


def mean(numbers):
    # Returns the arithmetic mean
    return float(sum(numbers)) / max(len(numbers), 1)


if __name__ == "__main__":
    random.seed(SEED)
    logger = Logger()

    # Generate appropriate number of test cases
    cases = [randomCardList(CARD_COUNT) for _ in range(TESTS)]

    # Run tests and collate results (side-effect of displaying data)
    for answer in cases:
        runGuess(answer, logger)
    
    logger.finalOutput()