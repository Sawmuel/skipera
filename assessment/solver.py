import time

import requests

from assessment.types import QUESTION_TYPE_MAP, MODEL_MAP, deep_blank_model, WHITELISTED_QUESTION_TYPES
from config import GRAPHQL_URL
from assessment.queries import (GET_STATE_QUERY, SAVE_RESPONSES_QUERY, SUBMIT_DRAFT_QUERY,
                                GRADING_STATUS_QUERY, INITIATE_ATTEMPT_QUERY, ABORT_ATTEMPT_QUERY)
from loguru import logger
from llm.connector import PerplexityConnector


class GradedSolver(object):
    def __init__(self, session: requests.Session, course_id: str, item_id: str):
        self.session: requests.Session = session
        self.course_id: str = course_id
        self.item_id: str = item_id
        self.attempt_id = None
        self.draft_id = None
        self.discarded_questions = []

    def solve(self):
        state = self.get_state()
        
        if state is None:
            logger.error("Could not retrieve assessment state. The assessment may not be accessible or may require prerequisites.")
            return

        if state["allowedAction"] == "RESUME_DRAFT":
            logger.warning("An attempt is already in progress, attempting to abort it...")
            if self.abort_attempt(state):
                logger.info("Successfully aborted previous attempt, starting new one...")
                # Retry after aborting
                state = self.get_state()
                if state is None or state["allowedAction"] != "START_NEW_ATTEMPT":
                    logger.error("Could not start new attempt after aborting. Please abort manually in Coursera.")
                    return
            else:
                logger.error("Could not abort attempt automatically. Please abort it manually in Coursera.")
                return

        if state["allowedAction"] == "START_NEW_ATTEMPT":
            if state["outcome"] is not None:
                if state["outcome"]["isPassed"]:
                    logger.debug("Already passed!")
                    return

            if state["attempts"]["attemptsRemaining"] == 0:
                logger.error("No more attempts can be made!")

            else:
                if not self.initiate_attempt():
                    logger.error("Could not start an attempt. Please file an issue.")

                else:
                    questions = self.retrieve_questions()
                    connector = PerplexityConnector()
                    answers = connector.get_response(questions)
                    
                    if answers is None:
                        logger.error("Could not get answers from LLM. Skipping this assessment.")
                        return

                    if not self.save_responses(answers["responses"]):
                        logger.error("Could not save responses. Please file an issue.")

                    else:
                        if not self.submit_draft():
                            logger.error("Could not submit the assignment. Please file an issue.")

                        else:
                            logger.debug("Waiting 10 seconds for grading..")
                            time.sleep(10)  # increased delay for grading process
                            if not self.get_grade():
                                logger.error("Sorry! Could not pass the assignment, maybe use a better model.")

        else:
            logger.error("Something went wrong! Please file an issue.")

    def get_state(self) -> dict:
        """
        Retrieves the current state of the assessment.
        """
        try:
            res = self.session.post(url=GRAPHQL_URL, params={
                "opname": "QueryState"
            }, json={
                "operationName": "QueryState",
                "variables": {
                    "courseId": self.course_id,
                    "itemId": self.item_id
                },
                "query": GET_STATE_QUERY
            }).json()

            if "data" in res and "SubmissionState" in res["data"]:
                return res["data"]["SubmissionState"]["queryState"]
            else:
                logger.error(f"Unexpected response format: {res}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving assessment state: {e}")
            return None

    def initiate_attempt(self) -> bool:
        """
        Initiates a new attempt for the assessment.
        """
        res = self.session.post(url=GRAPHQL_URL, params={
            "opname": "Submission_StartAttempt"
        }, json={
            "operationName": "Submission_StartAttempt",
            "variables": {
                "courseId": self.course_id,
                "itemId": self.item_id
            },
            "query": INITIATE_ATTEMPT_QUERY
        })

        if "Submission_StartAttemptSuccess" in res.text:
            return True
        return False

    def retrieve_questions(self) -> dict:
        """
        Retrieves the questions for the particular attempt
        which are to be sent to the LLM Connector.
        """
        state = self.get_state()
        draft = state["attempts"]["inProgressAttempt"]

        self.draft_id = draft["id"]
        self.attempt_id = draft["draft"]["id"]
        questions = draft["draft"]["parts"]
        questions_formatted = {}

        for question in questions:
            if not question["__typename"] in WHITELISTED_QUESTION_TYPES:
                self.discarded_questions.append({
                    "questionId": question["partId"],
                    "questionType": QUESTION_TYPE_MAP[question["__typename"]][1],
                    "questionResponse": {
                        QUESTION_TYPE_MAP[question["__typename"]][0]:
                        deep_blank_model(MODEL_MAP[question["__typename"]])
                    }
                })
                continue

            options = []
            for option in question["questionSchema"]["options"]:
                options.append({
                    "option_id": option["optionId"],
                    "value": option["display"]["cmlValue"]
                })

            questions_formatted[question["partId"]] = {"Question": question["questionSchema"]["prompt"]["cmlValue"],
                                                       "Options": options,
                                                       "Type": "Single-Choice" if
                                                       question["__typename"] == "Submission_MultipleChoiceQuestion"
                                                       else "Multi-Choice"}
        return questions_formatted

    def save_responses(self, answers: dict) -> bool:
        """
        Saves the responses for the assessment to the draft.
        """
        answer_responses = []

        for answer in answers:
            answer_responses.append({
                "questionId": answer["question_id"],
                "questionType": "MULTIPLE_CHOICE" if answer["type"] == "Single" else "CHECKBOX",
                "questionResponse": {
                    "multipleChoiceResponse" if answer["type"] == "Single" else "checkboxResponse": {
                        "chosen": answer["option_id"][0] if answer["type"] == "Single" else answer["option_id"]
                    }
                }
            })

        res = self.session.post(url=GRAPHQL_URL, params={
            "opname": "Submission_SaveResponses"
        }, json={
            "operationName": "Submission_SaveResponses",
            "variables": {
                "input": {
                    "courseId": self.course_id,
                    "itemId": self.item_id,
                    "attemptId": self.draft_id,
                    "questionResponses": [*answer_responses, *self.discarded_questions]
                }
            },
            "query": SAVE_RESPONSES_QUERY
        })

        if "Submission_SaveResponsesSuccess" in res.text:
            return True

        logger.debug([*answer_responses, *self.discarded_questions])
        logger.debug(res.json())
        return False

    def submit_draft(self) -> bool:
        """
        Submits the draft for evaluation after the submission is saved.
        """
        res = self.session.post(url=GRAPHQL_URL, params={
            "opname": "Submission_SubmitLatestDraft"
        }, json={
            "operationName": "Submission_SubmitLatestDraft",
            "query": SUBMIT_DRAFT_QUERY,
            "variables": {
                "input": {
                    "courseId": self.course_id,
                    "itemId": self.item_id,
                    "submissionId": self.attempt_id
                }
            }
        })

        if "Submission_SubmitLatestDraftSuccess" in res.text:
            return True
        return False

    def get_grade(self) -> bool:
        """
        Retrieves the outcome for the submitted assignment.
        """
        res = self.session.post(url=GRAPHQL_URL, params={
            "opname": "QueryState"
        }, json={
            "operationName": "QueryState",
            "query": GET_STATE_QUERY,
            "variables": {
                "courseId": self.course_id,
                "itemId": self.item_id
            }
        }).json()

        outcome = res["data"]["SubmissionState"]["queryState"]["outcome"]
        
        if outcome is None:
            logger.warning("Could not retrieve grade outcome. The assignment may still be grading.")
            return False

        logger.debug(f"Achieved {outcome['earnedGrade']} grade. Passed? {outcome['isPassed']}")

        return outcome['isPassed']

    def abort_attempt(self, state: dict) -> bool:
        """
        Aborts an in-progress attempt.
        """
        try:
            in_progress = state["attempts"].get("inProgressAttempt")
            if not in_progress:
                return False
            
            attempt_id = in_progress["id"]
            
            res = self.session.post(url=GRAPHQL_URL, params={
                "opname": "Submission_DiscardDraft"
            }, json={
                "operationName": "Submission_DiscardDraft",
                "variables": {
                    "attemptId": attempt_id
                },
                "query": ABORT_ATTEMPT_QUERY
            })
            
            if "Submission_DiscardDraftSuccess" in res.text:
                return True
            return False
        except Exception as e:
            logger.error(f"Error aborting attempt: {e}")
            return False
