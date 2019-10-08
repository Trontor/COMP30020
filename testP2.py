"""
:testing.py

:purpose: Run randomised math-puzzles to test implementation of COMP30026 Proj 2.
:author(s): Callum H

:requirements:
- Python 3
- Assumes you have numpy, pandas, and pyswip installed (for python 3)
- Place in same directory as 'proj2.pl' file (strictly named as such)
- Make a "Logs" folder in the SAME DIRECTORY as this and the 'proj2.pl' (if you want logs, that is)

:summary:
- Randomly generates math puzzles according to specification
- Randomly hides a number of values in each puzzle
- The size and # hidden values can be chosen or random for each puzzle
- Code then formats these param_puzzles into something that prolog can read

:flaws:
- Does not check if your program finds solutions to impossible puzzles.
"""

import pandas as pd
import numpy as np
import random as rand
import pyswip as swi
import datetime as dt
import os
import re
import time

SEED = 1337
N_TESTS = 10
TIMEOUT = 0.04
TIME_ACCURACY = 2

# Used when you request deterministic output
SIZE = 3
N_PARAMS = 7

# Adjust this if you want to use SIZE, N_PARAMS for entire suite. 
# The actual puzzles and param allocation will still be randomly generated.
RANDOMISED_DIMENSIONS = False
# Controls if you see the log printed out in terminal.
VERBOSE = True

OVERALL_BANNER = "\n============= Testing Summary =============\n"
LINE_ONE = "Outcomes:\n- Correct\t {:3d} ({:5.2f}%)\n- Wrong #'s\t {:3d} ({:5.2f}%)\n- Null\t\t {:3d} ({:5.2f}%)\n"
LINE_TWO = "- Error\t\t {:3d} ({:5.2f}%)\n- Timeout\t {:3d} ({:5.2f}%)\n- AVG Time\t{:.2f}\n- MAX Time\t{:.2f}\n"
OVERALL_SUMMARY = OVERALL_BANNER + LINE_ONE + LINE_TWO

def main():
    """
    Generates test cases and runs output in shell/terminal, collating results
    """
    rand.seed(SEED)
    logger = Logger()

    # Test case execution
    for _ in range(N_TESTS):
        # Choose your size and parameters
        if RANDOMISED_DIMENSIONS:
            size = rand.randint(2, 4)
            parameters = rand.randint(size, size**2)
        else:
            size = SIZE
            parameters = N_PARAMS
        
        # Generate puzzle string
        puzzle = random_param_puzzle(n=size, params=parameters)
        run_test(puzzle, logger)
    
    # Summary
    logger.summarise()
    logger.output()

class Logger:
    """
    A containment for entering and extracting
    data relevant to analysis and debugging.

    Functions:
        outcome -- For storing data pertaining to tests
        print -- For printing a string (side effect: print to log)
        summarise -- For collating and displaying test data (side effect: print to log)
        output -- Outputs log to file
    """

    def __init__(self):
        self.log_data = []
        self.log_len = 0
        self.print_log = ""

    def outcome(self, puzzle, time, outcome):
        if time >= TIMEOUT:
            self.print(f">> {outcome} || TIMEOUT ({time})")
        else:
            self.print(f">> {outcome}")
        self.log_data.append([puzzle, time, outcome])
        self.log_len += 1

    def print(self, string, coerce=False):
        """Logs something to be printed, as well as printing it."""
        self.print_log += f"{string}\n"
        if coerce or VERBOSE:
            print(string)
    
    def summarise(self):
        df = pd.DataFrame(self.log_data, columns = ["Puzzle", "TimeTaken", "Outcome"])
        total_tests = len(df)

        # extract log data
        total_correct = sum(df["Outcome"] == "Correct")
        total_wrong = sum(df["Outcome"] == "Wrong")
        total_null = sum(df["Outcome"] == "Null")
        total_error = total_tests - total_correct - total_wrong - total_null
        # NOTE: This is not mutually exclusive with other options above
        total_timeout = sum(df["TimeTaken"] >= TIMEOUT)
        average_time = df["TimeTaken"].mean()
        max_time = df["TimeTaken"].max()

        # Display test summary
        self.print(OVERALL_SUMMARY.format(
            total_correct, total_correct*100/total_tests, \
            total_wrong, total_wrong*100/total_tests, \
            total_null, total_null*100/total_tests, \
            total_error, total_error*100/total_tests, \
            total_timeout, total_timeout*100/total_tests, \
            average_time, max_time), coerce=True)

    def output(self):
        """
        Outputs a clean rundown of all data and results to a log file.
        """
        time = dt.datetime.strftime(dt.datetime.now(), '%b-%d %H-%M-%S')
        tag = input("Tag for file >> ")
        if RANDOMISED_DIMENSIONS:
            filename = f"Logs/{tag} - {SEED}-{N_TESTS}-Random - {time}.txt"
        else:
            filename = f"Logs/{tag} - {SEED}-{N_TESTS}-{SIZE}-{N_PARAMS} - {time}.txt"
        header = f"|=== LOG FOR {filename} ===|\n"
        
        # Open file
        fyle = open(filename, "a")
        fyle.write(header)
        
        fyle.write(self.print_log)
        fyle.close()

        print(f"\n>> Output execution to {filename}")

def run_test(array_puzzle, logger):
    """
    Runs a test on puzzle and outputs data on outcome to logger.
    """

    # String format to cohere with Prolog
    puzzle = str(array_puzzle.tolist()).replace("'","")
    
    logger.print(f"Test {1+logger.log_len}\t{puzzle}", coerce=True)

    # Run test
    timeStarted = time.time()
    prolog = swi.Prolog()
    try:
        # Access file
        prolog.consult(f"{os.getcwd()}\\proj2.pl".replace("\\","/"))

        # NOTE: Outcome is of form [] i.e. false, [{}] i.e. true OR [{'A':1,'B':2,etc.}]
        outcome = list(prolog.query(f'puzzle_solution({puzzle})'))
        timeDelta = round(time.time() - timeStarted, TIME_ACCURACY)
    except Exception as e:
        timeDelta = round(time.time() - timeStarted, TIME_ACCURACY)
        logger.outcome(puzzle, timeDelta, "Error")
        logger.print(f"ERROR: {str(e)}")
        return
    
    if len(outcome):
        # Verify correctness
        if valid_soln(array_puzzle, outcome[0], logger):
            logger.outcome(puzzle, timeDelta, "Correct")
        else:
            logger.outcome(puzzle, timeDelta, "Wrong")
    else:
        # Log unsolvable
        logger.outcome(puzzle, timeDelta, "Null")

def random_param_puzzle(n, params):
    """
    Adds random parametrisation of inner values to finalise a test case.
    :puzzle: complete valid puzzle.
    :n: number of nonheader values per row/col
    :params: number of values to hide
    """
    
    assert(0 <= params <= n**2)

    # Generate puzzle
    puzzle = random_puzzle(n)
    
    # Fetch random element indices. Add 1 due to headers
    index_range = range(1,n+1)
    random_values = rand.sample([(i,j) for i in index_range \
        for j in index_range], params)

    # Replace with parameters. 
    # NOTE: Customisable, be careful as program does lazy parsing (e.g. X11 will be confused with X1)
    params = [f'_X{i}_' for i in range(params)]
    puzzle = puzzle.astype(str)
    for index, p in zip(random_values, params):
        puzzle[index] = p

    return puzzle

def random_base(n):
    """
    'Efficient' construction of a new random puzzle 
    :n: Number of (nonheader) values per row/col
    """

    # Diagonal
    diagonal_val = rand.randint(1,9)
    rows = np.zeros(n)
    for row in range(n):
        newrow = [0]*n
        for col in range(n):
            # Diagonal
            if col == row:
                newrow[col] = diagonal_val
            else:
                if row == 0:
                    colpriors = [0]
                else:
                    colpriors = rows[:,col]
                priors = set(colpriors).union(set(newrow))
                newrow[col] = rand.sample(set(range(1,10)).difference(priors), 1)[0]
        rows = np.vstack((rows, newrow))
    return rows[1:]

def random_puzzle(n):
    """
    Defines base values (internals), headers and constructs valid puzzle
    :n: number of (nonheader) values per row/col
    """

    # Get valid internal values
    while True:
        try:
            base = random_base(n).astype(int)
            assert(valid_base(base))
            break
        except:
            continue

    # Randomly define headers
    operands = (np.sum, np.prod)
    row_headers = np.array([rand.choice(operands)(base[i]) for i in range(n)])
    col_headers = np.array([0] + [rand.choice(operands)(base[:,i]) for i in range(n)])

    # Append
    puzzle = np.concatenate((row_headers[:, np.newaxis], base), axis=1)
    puzzle = np.vstack((col_headers, puzzle))
    return puzzle

def valid_soln(puzzle, assigns, logger):
    """
    Verifies a solution.
    :puzzle: numpy array of full puzzle (with parameters)
    :assigns: output of prolog execution (may/may not have parameter assignments as a dict)
    :logger: Logger instance
    """

    # Printing
    str_assigns = ', '.join(map(lambda k: f"{k} = {assigns[k]}",sorted(assigns)))
    logger.print(f">> Verifying that {str_assigns}")

    # Replace values. Sort assigns to prevent X1 replacing in X11
    answer = puzzle.copy()
    for v in assigns:
        answer = np.where(answer==v,assigns[v],answer)
    answer = answer.astype(int)

    # Verify internals, then sum/product relationships
    if valid_base(answer[1:,1:]):
        N = answer.shape[1] # 1 + # rows
        for row in range(1,N):
            vals = answer[row, 1:]
            header = answer[row, 0]
            if header not in [np.sum(vals), np.prod(vals)]:
                logger.print(f">> INVALID: {header} doesn't match with {vals}")
                return False
        for col in range(1,N):
            vals = answer[1:, col]
            header = answer[0, col]
            if header not in [np.sum(vals), np.prod(vals)]:
                logger.print(f">> INVALID: {header} doesn't match with {vals}")
                return False
        return True
    else:
        logger.print(f">> INVALID: Values don't comply with domain/uniqueness restrictions")
        return False

def valid_base(arr):
    """
    Checks validity of randomised inner values: for debugging purpose really
    :arr: the incomplete puzzle (inner values only) to test
    """

    return all([sorted(list(x)) == list(set(x)) for x in arr] + \
        [sorted(list(x)) == list(set(x)) for x in np.transpose(arr)]) and \
        all(np.vectorize(lambda x: 0 < x < 10)(arr.flatten())) and \
            1 == len(set(np.diag(arr)))

if __name__ == "__main__":
    main()