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
import datetime as dt
import sys

GUESS_REGEX = r"in (.*) guesses"
QUALITY_REGEX = r"Approximate quality = (.*)%"
ACCURACY = 2
TESTS = 10
CARD_COUNT = 4
TESTS = 500
CARD_COUNT = 2
SEED = 1337
TIMEOUT = 10
COMPILE_TARGET = "Proj1test"

DISPLAY_HEADER =  "Total Runs: {0} | {1} | "
DISPLAY_DATA = "Guesses: Min {0} - Avg {1:.2f} - Max {2}  ||  Max Time {3:.2f}  ||  Quality: Min {4:.2f} - Avg {5:.2f}"


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
        self.printLog = ""

    def logPrint(self, string):
        """Logs something to be printed, as well as printing it."""
        self.printLog += string + "\n"
        print(string)

    def logError(self, cardInput):
        """Store the data for an error that has occurred."""
        self.erroneousInputs.append((test_no, cardInput))

    def logSuccess(self, cardInput, guessCount, guessQuality, guessTime):
        """Append data of a successful test to the dataframe."""
        self.data.append([cardInput, len(cardInput), guessCount, guessQuality, guessTime])
    
    def getDataFrame(self):
        return DataFrame(self.data, columns=["Answer", "cardCount", "Guesses", "Quality", "TimeTaken"])

    def summarise(self, data=None):
        """Calculates and displays desired fields to summarise data.

        Arguments:
            data [abstract] -- Will be printed if passed, e.g. the actual card state
        """

        df = self.getDataFrame()
        numericData = df[["Guesses", "Quality", "TimeTaken"]]
        totalTests = len(df)

        # Display data
        header = DISPLAY_HEADER.format(totalRuns, (data if not None else ""))
        data = DISPLAY_DATA.format(minGuess, averageGuess, maxGuess, maxTime, minQuality, averageQuality)
        return header + data
    
    def finalOutput(self):
        totalTime = sum(map(lambda x : x[4], self.data))
        self.logPrint(f"Completed in {totalTime:.2f} seconds.")
        
        if len(self.erroneousInputs) > 0:
            self.logPrint("Answers that were failed: ")
            for answer in self.erroneousInputs:
                self.logPrint(answer)
        else:
            self.logPrint("No errors were encountered!")
        
        # Report back distribution of quality, and 'worstcase' values
        df = self.getDataFrame()
        self.logPrint("\n" + self.summarise())
        self.logPrint(f"\nYour distribution of Guesses:\n{df['Guesses'].value_counts().sort_index()}")
        lower_thresh = 4
        upper_thresh = 5
        if len(df["Answer"][0]) <= 2:
            thresh = lower_thresh
        else:
            thresh = upper_thresh

        worstMeasurements = df.loc[df['Guesses'] > thresh, ["Answer", "Guesses", "Quality", "TimeTaken"]].sort_values(["Guesses"])
        self.logPrint(f"\nYour worst measurements:\n{worstMeasurements}")
    
    def outputLog(self):
        """Outputs a clean rundown of all data and results to a log file."""
        time = dt.datetime.strftime(dt.datetime.now(), 'Log %Y-%m-%d -- %H-%M-%S')
        name = input("Name tag for file >> ")
        filename = f"Logs/{name}-{SEED}-{CARD_COUNT}-{TESTS}-{time}.txt"
        header = f"|=== LOG FOR {time} ===|\n"
        
        # Open file
        fyle = open(filename, "a")
        fyle.write(header)
        
        fyle.write(self.printLog)
        fyle.close()

        print(f"\n>> Output execution to {filename}")

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
            print(logger.summarise(data))
    except IndexError:
        # The program did not execute successfully.
        if display:
            logger.logPrint(f">> ERROR OCCURRED WITH {answer}. Continuing with analysis\n")
        logger.logError(answer)


def mean(numbers):
    # Returns the arithmetic mean
    return float(sum(numbers)) / max(len(numbers), 1)


if __name__ == "__main__":
    compile()
    random.seed(SEED)
    logger = Logger()

    os.system("ghc -O2 --make Proj1Test")

    # Generate appropriate number of test cases
    cases = [randomCardList(CARD_COUNT) for _ in range(TESTS)]

    # Run tests and collate results (side-effect of displaying data)
    print("Running Test Cases...\n")
    for test_no, answer in enumerate(cases):
        runGuess(test_no + 1, answer, logger)
    print()

    logger.finalOutput()
    logger.outputLog()