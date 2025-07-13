import re
import pdfplumber
import json
import os

def parse_exam_pdf(pdf_path):
    """
    Parses an ExamTools results PDF to extract:
    - The applicant's name
    - A list of missed questions with their designators, chosen answers, and correct answers

    Args:
        pdf_path (str): Path to the uploaded PDF file

    Returns:
        tuple: (applicant_name (str or None), missed_questions (list of dict))
    """
    missed_questions = []
    applicant_name = None

    # Regex to extract lines like: "1. T6B02: A (should be C)"
    line_regex = re.compile(r'\d+\.\s+([TGE]\d[A-Z]\d{2}):\s+([A-D])(?:\s+\(should be\s+([A-D])\))?')

    # Regex to extract applicant name from line like: "Enzo B Cabral (PIN: 5341)"
    name_regex = re.compile(r'^([A-Za-z\'\- ]+)\s+\(PIN:\s*\d{4}\)(?:\s+PASS)?$')

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            width = page.width
            height = page.height
            text = page.extract_text()

            # On first page, try to extract applicant name from top lines
            if page_num == 0:
                for line in text.split('\n'):
                    name_match = name_regex.match(line.strip())
                    if name_match:
                        applicant_name = name_match.group(1).strip()
                        break

            # Define bounding boxes for left and right columns
            left_bbox = (0, 0, width / 2, height)
            right_bbox = (width / 2, 0, width, height)

            # Extract text from both columns
            left_text = page.crop(left_bbox).extract_text()
            right_text = page.crop(right_bbox).extract_text()

            # Combine lines from both columns
            all_lines = []
            if left_text:
                all_lines.extend(left_text.split('\n'))
            if right_text:
                all_lines.extend(right_text.split('\n'))

            # Parse each line for missed questions
            for line in all_lines:
                match = line_regex.search(line)
                if match:
                    designator = match.group(1)
                    chosen = match.group(2)
                    correct = match.group(3) if match.group(3) else chosen
                    if chosen != correct:
                        missed_questions.append({
                            "designator": designator,
                            "chosen": chosen,
                            "correct": correct
                        })

    # Sort missed questions by designator (e.g., T1A01, T1A02)
    missed_questions.sort(key=lambda x: x['designator'])
    return applicant_name, missed_questions

def load_question_pool(first_designator):
    """
    Loads the correct question pool JSON based on the designator.

    Args:
        first_designator (str): e.g., 'T1A01', 'G4B02', 'E1A05'

    Returns:
        dict: Mapping of designator IDs to question data
    """
    pool_file_map = {
        'T': 'technician.json',
        'G': 'general.json',
        'E': 'extra.json'
    }
    pool_key = first_designator[0].upper()
    pool_file = os.path.join('data', pool_file_map.get(pool_key))

    if not pool_file or not os.path.exists(pool_file):
        raise FileNotFoundError(f"Question pool file '{pool_file}' not found for designator '{first_designator}'")

    with open(pool_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Build a dict { 'T1A01': {...}, 'T1A02': {...}, ... }
    return { q['id']: q for q in data }

def build_detailed_report(missed, question_pool):
    """
    Builds a detailed report for each missed question, combining:
    - Question text
    - Answer letter and full answer text (chosen and correct)

    Args:
        missed (list of dict): List from parse_exam_pdf()
        question_pool (dict): Mapping from load_question_pool()

    Returns:
        list of dict: Detailed report per missed question
    """
    detailed_report = []
    for m in missed:
        q = question_pool.get(m['designator'])
        if not q:
            # Question not found in pool — fallback text
            detailed_report.append({
                "designator": m['designator'],
                "question": "(Question text not found)",
                "your_answer_letter": m['chosen'],
                "your_answer_text": "(Unknown)",
                "correct_answer_letter": m['correct'],
                "correct_answer_text": "(Unknown)"
            })
            continue

        # Convert letter (A-D) to index (0-3) for answer text lookup
        your_index = 'ABCD'.index(m['chosen'])
        correct_index = 'ABCD'.index(m['correct'])

        detailed_report.append({
            "designator": m['designator'],
            "question": q['question'],
            "your_answer_letter": m['chosen'],
            "your_answer_text": q['answers'][your_index],
            "correct_answer_letter": m['correct'],
            "correct_answer_text": q['answers'][correct_index]
        })

    return detailed_report