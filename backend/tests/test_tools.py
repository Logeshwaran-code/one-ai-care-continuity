from app.routers.tools import _simple_answer
from app.llm import load_prompt


def test_simple_answer_explains_safe_health_questions():
    answer = _simple_answer("What is blood pressure?", "en")
    assert "top number" in answer and "care team" in answer


def test_simple_answer_has_safe_fallback():
    answer = _simple_answer("Tell me something", "en")
    assert "specific question" in answer


def test_question_answer_prompt_contains_user_question():
    prompt, _ = load_prompt("question_answer")
    rendered = prompt.safe_substitute(question="What is a fever?", language="en")
    assert "What is a fever?" in rendered
