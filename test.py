"""
:name: test.py
:author: Rohyl Joshi, Callum Holmes, Shevon Mendis
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
TESTS = 10
CARD_COUNT = 4
SEED = 1337
TIMEOUT = 10
COMPILE_TARGET = "Proj1test"

SINGLE_TEST_SUMMARY = ">> Results: No. of Guesses: {1} | Quality: {2} | Execution Time: {3}s\n"
OVERALL_SUMMARY = "== Metrics ==\n\nGUESSES:\nMin: {0}\nMax: {1}\nAvg: {2:.2f}\n\nTIME:\nMin: {3:.2f}\nMax: {4:.2f}\nAvg: {5:.2f}\n\nQUALITY:\nMin: {6:.2f}\nMax: {7:.2f}\nAvg: {8:.2f}\n\n============="


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

    def logError(self, test_no, cardInput):
        """Store the data for an error that has occurred."""
        self.erroneousInputs.append((test_no, cardInput))

    def logSuccess(self, cardInput, guessCount, guessQuality, guessTime):
        """Append data of a successful test to the dataframe."""
        self.data.append([cardInput, len(cardInput),
                          guessCount, guessQuality, guessTime])

    def summarise(self, data):
        """Calculates and displays desired fields to summarise data.

        Arguments:
            data [abstract] -- Will be printed if passed, e.g. the actual card state
        """

        df = DataFrame(self.data, columns=[
                       "Answer", "cardCount", "Guesses", "Quality", "TimeTaken"])
        numericData = df[["Guesses", "Quality", "TimeTaken"]]
        totalTests = len(df)

        # extract log data
        self.averageGuess, self.averageQuality, self.averageTime = numericData.agg(
            mean)[["Guesses", "Quality", "TimeTaken"]]
        self.maxTime, self.maxGuess, self.maxQuality = numericData.max()[
            ["TimeTaken", "Guesses", "Quality"]]
        self.minTime, self.minGuess, self.minQuality = numericData.min()[
            ["TimeTaken", "Guesses", "Quality"]]

        # Display test summary
        print(SINGLE_TEST_SUMMARY.format(
            totalTests, data[1], data[2], data[3]))

    def finalOutput(self):
        print("============= Testing Summary =============\n")
        print(f"Cards: {CARD_COUNT}\nTests:{TESTS}\nSeed:{SEED}\n")

        totalTime = sum(map(lambda x: x[4], self.data))
        print(f"Completed in {totalTime:.2f} seconds.")

        if len(self.erroneousInputs) > 0:
            print("\nTest Cases that failed: \n")
            for test_no, answer in self.erroneousInputs:
                cards = ""
                for card in answer:
                    cards += f"'{card}' "
                print(f" - Test #{test_no}: {cards}")
            print()
        else:
            print("No errors were encountered! Well Done :)\n")

        print(OVERALL_SUMMARY.format(self.minGuess, self.maxGuess,
                                     self.averageGuess, self.minTime,
                                     self.maxTime, self.averageTime,
                                     self.minQuality, self.maxQuality,
                                     self.averageQuality))

        print("\n===========================================")


def compile(optimisation=True):
    print(f"Compiling {COMPILE_TARGET}...", end="")
    optimisationArg = "-O2" if optimisation else ""
    args = f"ghc {optimisationArg} --make {COMPILE_TARGET}"

    # windows config
    if sys.platform in ["win32", "cgywin"]:
        status = subprocess.call(args)
    # assuming that the only other OS being used to run this script is mac
    else:
        status = subprocess.call(args, shell=True)

    # exit if code failed to compile
    if status != 0:
        print("Failed- please check your code!")
        sys.exit()

    print("Success\n")


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


def runGuess(test_no, answer, logger, display=True):
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

    print(f"Test #{test_no}")

    cards = ""
    for card in answer:
        cards += f"'{card}' "

    print(f">> Running: ./{COMPILE_TARGET} {cards}")

    # windows config
    if sys.platform in ["win32", "cygwin"]:
        args = [f"./{COMPILE_TARGET}.exe"] + answer
    # assuming that the only other OS being used to run this script is mac
    else:
        args = [f"./{COMPILE_TARGET}"] + answer

    try:
        timeStarted = time.time()
        output = subprocess.check_output(args, timeout=TIMEOUT).decode('utf-8')
        # Uncomment to see the output of the Proj1Test script
        # print(output)
        timeDelta = round(time.time() - timeStarted, ACCURACY)
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
                f">> Results: TIMEOUT (>{TIMEOUT}s)\n")
        # TODO: note that this input timed out
        logger.logError(test_no, answer)
    except IndexError:
        # The program did not execute successfully.
        if display:
            print(
                f">> ERROR OCCURRED WITH {answer}. Continuing with analysis\n")
        logger.logError(test_no, answer)


def mean(numbers):
    # Returns the arithmetic mean
    return float(sum(numbers)) / max(len(numbers), 1)


if __name__ == "__main__":
    compile()
    random.seed(SEED)
    logger = Logger()

    # Generate appropriate number of test cases
    cases = [randomCardList(CARD_COUNT) for _ in range(TESTS)]

    # Run tests and collate results (side-effect of displaying data)
    print("Running Test Cases...\n")
    for test_no, answer in enumerate(cases):
        runGuess(test_no + 1, answer, logger)
    print()

    logger.finalOutput()
