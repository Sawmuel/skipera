# https://github.com/serv0id/skipera
import json
import requests
from config import PERPLEXITY_API_URL, PERPLEXITY_API_KEY, PERPLEXITY_MODEL
from pydantic import BaseModel
from typing import List, Literal
from loguru import logger


class ResponseFormat(BaseModel):
    question_id: str
    option_id: List[str]
    type: Literal["Single", "Multi"]


class ResponseList(BaseModel):
    responses: List[ResponseFormat]


class PerplexityConnector(object):
    def __init__(self):
        self.API_URL: str = PERPLEXITY_API_URL
        self.API_KEY: str = PERPLEXITY_API_KEY

    def get_response(self, questions: dict) -> dict:
        """
        Sends the questions to Perplexity and asks for the answers
        in a JSON format.
        """
        if not self.API_KEY or self.API_KEY == "":
            logger.error("Perplexity API Key is not configured in config.py!")
            return None
            
        logger.debug("Making an API Request to Perplexity..")
        
        try:
            response = requests.post(url=self.API_URL, headers={
                "Authorization": f"Bearer {self.API_KEY}"
            }, json={
                "model": PERPLEXITY_MODEL,
                "messages": [
                    {"role": "system", "content": 
                        "You are an expert assistant that answers multiple choice questions accurately. "
                        "You will receive questions in JSON format with question text and answer options. "
                        "Each option has an 'option_id' (which you MUST return) and a 'value' (the answer text). "
                        "Your task:\n"
                        "1. Read each question carefully, ignoring any HTML tags in the text\n"
                        "2. Analyze all available options\n"
                        "3. Select the CORRECT option(s) based on your knowledge\n"
                        "4. For 'Single-Choice' questions: return ONLY ONE option_id in an array\n"
                        "5. For 'Multi-Choice' questions: return ALL correct option_ids in an array\n"
                        "6. CRITICAL: You MUST return the 'option_id' value exactly as provided, NOT the answer text\n"
                        "7. Think step by step and choose the most accurate answer(s)\n"
                        "8. If unsure, use logical reasoning and domain knowledge to make the best choice"
                    },
                    {"role": "user", "content": 
                        "Answer these questions. Return the response in the exact JSON schema format specified.\n\n"
                        "IMPORTANT: In your response, 'option_id' must be the ID from the options provided, "
                        "NOT a number or the answer text itself.\n\n"
                        f"Questions:\n{json.dumps(questions, indent=2)}"
                    },
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"schema": ResponseList.model_json_schema()}
                },
                "temperature": 0.2  # Lower temperature for more consistent/accurate responses
            })
            
            if response.status_code == 401:
                logger.error("Perplexity API Key is invalid or unauthorized (401). Please check your API key in config.py")
                return None
            elif response.status_code != 200:
                logger.error(f"Perplexity API error: Status {response.status_code} - {response.text}")
                return None
                
            response_json = response.json()
            return json.loads(response_json["choices"][0]["message"]["content"])
            
        except Exception as e:
            logger.error(f"Error connecting to Perplexity API: {e}")
            return None
