import httpx
import json
import logging
from ..rag.inference import OLLAMA_URL, LLM_MODEL

logger = logging.getLogger(__name__)

ASSESSMENT_PROMPT = """You are Smiley, an expert curriculum designer.
Based on the provided textbook context, generate a multiple-choice quiz.
Return the quiz STRICTLY as a JSON object containing a "questions" key which is a list of question objects.
Each question object must have: 'question', 'options' (array of 4 strings), 'correct_answer', and 'explanation'.
Example:
{
  "questions": [
    {
      "question": "question text",
      "options": ["opt1", "opt2", "opt3", "opt4"],
      "correct_answer": "correct option text matching one of options",
      "explanation": "why this option is correct"
    }
  ]
}
Do not include markdown blocks or any other explanation, just the raw JSON object."""

class AssessmentGenerator:
    @staticmethod
    async def generate_questions(context_text: str, topic: str, difficulty: str, count: int) -> list:
        """
        Communicates with local Ollama instance to generate multiple-choice questions
        specifically scoped to context text and difficulty levels.
        """
        prompt = f"""Context:
{context_text}

Topic: {topic}
Difficulty: {difficulty} (easy, medium, or hard)
Number of Questions: {count}

Please generate the JSON quiz with exactly {count} multiple choice questions."""

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": ASSESSMENT_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.3
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_URL, json=payload, timeout=90.0)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama returned status code {response.status_code}")
            
            data = response.json()
            if "message" in data and "content" in data["message"]:
                response_text = data["message"]["content"].strip()
            else:
                response_text = data.get("response", "[]").strip()
            print(f"DEBUG: Ollama raw response: {response_text}")
            try:
                questions = json.loads(response_text)
                if isinstance(questions, dict):
                    for k, v in questions.items():
                        if isinstance(v, list):
                            questions = v
                            break
                if not isinstance(questions, list):
                    questions = []
                return questions
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse generated assessment JSON: {e}. Raw response: {response_text}")
                raise e
