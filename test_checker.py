import random
import string

def generate_test_code(length=6):
    """Tasodifiy test kodi generatsiya qilish"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def parse_answers(answers_text):
    """
    Test kalitlarini parse qilish.
    Format: "1A2B3C4D5A6B7C8D..." yoki "1-A 2-B 3-C ..."
    Returns: {1: 'A', 2: 'B', ...}
    """
    answers = {}

    # Format: "1A2B3C4D" (raqam + harf)
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

def check_answers(correct_answers: dict, user_answers_text: str):
    """
    Foydalanuvchi javoblarini tekshirish.
    user_answers_text: "1A2B3C4D..." yoki "ABCDA..."
    Returns: (score, total, percentage, detailed)
    """
    user_answers = parse_answers(user_answers_text)

    if not user_answers:
        # Faqat harflar formatida: "ABCDAB..."
        letters = user_answers_text.upper().replace(" ", "")
        user_answers = {i+1: l for i, l in enumerate(letters) if l.isalpha()}

    total = len(correct_answers)
    score = 0
    detailed = {}

    for q_num, correct in correct_answers.items():
        user_ans = user_answers.get(q_num, "?")
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

def format_detailed_result(detailed: dict, max_show=30):
    """Batafsil natija formatlash"""
    lines = []
    for q_num in sorted(detailed.keys())[:max_show]:
        d = detailed[q_num]
        icon = "✅" if d["is_correct"] else "❌"
        lines.append(f"{icon} {q_num}-savol: Siz={d['user']} | To'g'ri={d['correct']}")
    if len(detailed) > max_show:
        lines.append(f"... va yana {len(detailed) - max_show} ta savol")
    return "\n".join(lines)

def answers_dict_to_string(answers: dict):
    """Dict ni string formatga o'tkazish: {1:'A', 2:'B'} -> '1A2B'"""
    return "".join(f"{k}{v}" for k, v in sorted(answers.items()))
