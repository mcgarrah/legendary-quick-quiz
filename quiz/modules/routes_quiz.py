"""
Copyright © 2024 J. Michael McGarrah <mcgarrah@gmail.com>
"""
import json
import random
from markupsafe import escape
from flask import render_template, request, jsonify
from quiz.modules.models import Question, Setting

def quiz(category_id):
    """
    Retrieves questions based on the category ID.
    Reads timer and number of questions settings.
    Randomly shuffles the questions.
    Conditionally shuffles the question options based on the no_shuffle attribute.
    Serializes the questions and renders the quiz template.
    """
    questions = Question.query.filter_by(category_id=category_id).all()
    timer_setting = Setting.query.filter_by(name='timer_duration').first()
    num_questions_setting = Setting.query.filter_by(name='num_questions').first()
    timer_duration = int(timer_setting.value) if timer_setting else 300
    num_questions = int(num_questions_setting.value) if num_questions_setting else 5

    random.shuffle(questions)
    selected_questions = questions[:num_questions]

    serialized_questions = []
    for question in selected_questions:
        try:
            options = [escape(option) for option in json.loads(question.options)]
            # Only shuffle the options if "no_shuffle" is False
            if not question.no_shuffle:
                random.shuffle(options)
        except json.JSONDecodeError:
            options = []  # Provide a default empty list if JSON decoding fails

        serialized_questions.append({
            'id': question.id,
            'question': escape(question.question),  # Escape the question text
            'options': options,
            'answer': escape(question.answer),  # Escape the correct answer
            'answer_details': escape(question.answer_details) if question.answer_details else None  # Escape the answer details
        })

    return render_template('quiz.html', questions=serialized_questions, timer_duration=timer_duration)

def check_answers():
    """
    Processes the user's answers.
    Compares them with the correct answers.
    Calculates the score and returns the results in JSON format.
    """
    data = request.json
    user_answers = [escape(answer) for answer in data['answers']]  # Escape user answers
    question_ids = data['question_ids']
    question_ids = [int(qid) for qid in question_ids]
    questions = {question.id: question for question in Question.query.filter(Question.id.in_(question_ids)).all()}
    sorted_questions = [questions[qid] for qid in question_ids]

    results = []
    score = 0
    for i, question in enumerate(sorted_questions):
        correct = question.answer == user_answers[i]
        if correct:
            score += 1
        results.append({
            'question': escape(question.question),  # Escape the question text
            'correct': correct,
            'answer': escape(question.answer),  # Escape the correct answer
            'answer_details': escape(question.answer_details) if question.answer_details else None,  # Escape the answer details
            'user_answer': user_answers[i]  # User answers are already escaped
        })

    return jsonify({'score': score, 'total': len(sorted_questions), 'results': results})