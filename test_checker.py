import random
import string

def generate_test_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def parse_answers(answers_text):
    answers = {}
    text = answers_text.upper().replace(" ", "").replace("-", "").replace(".", "").replace(",", "")
    i = 0
    while i < len(text):
        num_str = ""
        while i < len(text) and text[i].isdigit():
            num_str += text[i]
            i += 1
        if num_str and i < len(text) and text[i].isalpha():
            answers[int(num_str)] = text[i]
            i += 1
        else:
            i += 1
    return answers

def check_answers(correct_answers: dict, user_answers: dict):
    total = len(correct_answers)
    score = 0
    detailed = {}
    for q_num, correct in correct_answers.items():
        user_ans = user_answers.get(str(q_num), user_answers.get(q_num, "?"))
        is_correct = user_ans == correct
        if is_correct:
            score += 1
        detailed[q_num] = {
            "correct": correct,
            "user": user_ans,
            "is_correct": is_correct
        }
    percentage = (score / total * 100) if total > 0 else 0
    return score, total, percentage, detailed

def answers_dict_to_string(answers: dict):
    return "".join(f"{k}{v}" for k, v in sorted(answers.items()))

def parse_answers_to_dict(answers_str: str) -> dict:
    parsed = parse_answers(answers_str)
    return {str(k): v for k, v in parsed.items()}
