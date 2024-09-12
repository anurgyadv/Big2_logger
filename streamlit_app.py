import streamlit as st
import types
import sys
import time
import logging
from io import StringIO
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Classes
class Trick:
    def __init__(self, playerNum: int, cards: List[str]):
        self.playerNum = playerNum
        self.cards = cards

class GameHistory:
    def __init__(self, finished: bool, winnerPlayerNum: int, gameHistory: List[List[Trick]]):
        self.finished = finished
        self.winnerPlayerNum = winnerPlayerNum
        self.gameHistory = gameHistory

class Player:
    def __init__(self, points: int, handSize: int):
        self.points = points
        self.handSize = handSize

class MatchState:
    def __init__(self, myPlayerNum: int, players: List[Player], myHand: List[str], toBeat: Trick | None, matchHistory: List[GameHistory], myData: str):
        self.myPlayerNum = myPlayerNum
        self.players = players
        self.myHand = myHand
        self.toBeat = toBeat
        self.matchHistory = matchHistory
        self.myData = myData

def load_algorithm_from_string(code_string):
    module = types.ModuleType("user_algorithm")
    exec(code_string, module.__dict__)
    return module

def log_message(message):
    st.write(message)
    logging.info(message)

def run_tests(algorithm_class):
    ai = algorithm_class()

    def test_case(name, state, expected_action):
        log_message(f"\nRunning test case: {name}")
        start_time = time.time()
        try:
            # Get the action from the AI
            action, _ = ai.getAction(state)
            end_time = time.time()
            
            # Compare the action with the expected output
            log_message(f"Action returned: {action}")
            log_message(f"Time taken: {end_time - start_time:.2f} seconds")
            
            assert action == expected_action, f"Test case '{name}' failed. Expected {expected_action}, got {action}"
            log_message("Test case passed!")
            return True
        except Exception as e:
            # Log the error and continue
            log_message(f"An error occurred in test case '{name}': {str(e)}")
            return False

    # Define your test cases
    test_cases = [
        {
            "name": "Beat opponent's pair",
            "state": MatchState(
                myPlayerNum=0,
                players=[Player(0, 13) for _ in range(4)],
                myHand=['4D', '4H', '7S', '9C', 'JD', 'KH', '2S'],
                toBeat=Trick(1, ['3D', '3H']),
                matchHistory=[GameHistory(False, -1, [])],
                myData=""
            ),
            "expected_action": ['4D', '4H']
        },
        {
            "name": "Pass when can't beat",
            "state": MatchState(
                myPlayerNum=0,
                players=[Player(0, 13) for _ in range(4)],
                myHand=['4D', '5H', '7S', '9C', 'JD', 'KH', 'AS'],
                toBeat=Trick(1, ['2D', '2H']),
                matchHistory=[GameHistory(False, -1, [])],
                myData=""
            ),
            "expected_action": []
        },
        {
            "name": "Play a straight",
            "state": MatchState(
                myPlayerNum=0,
                players=[Player(0, 13) for _ in range(4)],
                myHand=['3D', '4H', '5S', '6C', '7D', 'JD', 'KH', '2S'],
                toBeat=None,
                matchHistory=[GameHistory(False, -1, [])],
                myData=""
            ),
            "expected_action": ['3D', '4H', '5S', '6C', '7D']
        },
        {
            "name": "Flush beats straight",
            "state": MatchState(
                myPlayerNum=0,
                players=[Player(0, 13) for _ in range(4)],
                myHand=['3D', '5D', '7D', '9D', 'JD', 'KH', '2S'],
                toBeat=Trick(1, ['4H', '5S', '6C', '7D', '8D']),
                matchHistory=[GameHistory(False, -1, [])],
                myData=""
            ),
            "expected_action": ['3D', '5D', '7D', '9D', 'JD']
        },
        {
            "name": "Four-of-a-kind beats full house",
            "state": MatchState(
                myPlayerNum=0,
                players=[Player(0, 13) for _ in range(4)],
                myHand=['6D', '6S', '6H', '6C', 'JD', 'KH', '2S'],
                toBeat=Trick(1, ['5D', '5S', '5H', '8C', '8S']),
                matchHistory=[GameHistory(False, -1, [])],
                myData=""
            ),
            "expected_action": ['6D', '6S', '6H', '6C', 'JD']
        },
        {
            "name": "Straight flush beats flush",
            "state": MatchState(
                myPlayerNum=0,
                players=[Player(0, 13) for _ in range(4)],
                myHand=['3D', '4D', '5D', '6D', '7D', 'KH', '2S'],
                toBeat=Trick(1, ['2H', '5H', '7H', '8H', '9H']),
                matchHistory=[GameHistory(False, -1, [])],
                myData=""
            ),
            "expected_action": ['3D', '4D', '5D', '6D', '7D']
        },
    ]

    # Run each test case and log the results
    passed_tests = 0
    total_tests = len(test_cases)
    for case in test_cases:
        if test_case(case["name"], case["state"], case["expected_action"]):
            passed_tests += 1

    log_message(f"\nAll test cases completed! Passed {passed_tests} out of {total_tests} tests.")
    return passed_tests, total_tests

def main():
    st.title("Big Two AI Tester")

    uploaded_file = st.file_uploader("Upload your text file containing the Algorithm class", type="txt")

    if uploaded_file is not None:
        st.write("File uploaded successfully!")
        
        # Read the content of the uploaded file
        code_content = uploaded_file.getvalue().decode("utf-8")
        
        # Load the module
        try:
            module = load_algorithm_from_string(code_content)
            
            if hasattr(module, 'Algorithm'):
                st.write("Algorithm class found in the uploaded file.")
                if st.button("Run Tests"):
                    st.write("Running tests...")
                    passed_tests, total_tests = run_tests(module.Algorithm)
                    st.write(f"Tests completed. Passed {passed_tests} out of {total_tests} tests.")
            else:
                st.error("No Algorithm class found in the uploaded file. Please make sure your file contains an Algorithm class.")
        except Exception as e:
            st.error(f"An error occurred while loading the Algorithm class: {str(e)}")
            st.error("Please make sure your file contains a valid Python class named 'Algorithm'.")

if __name__ == "__main__":
    main()
