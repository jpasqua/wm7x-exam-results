import re
import pdfplumber
import json
import os

def parse_exam_pdf(pdf_path):
    """
    Parses a multi-exam PDF and returns:
    - applicant_name (str or None)
    - results: list of exam results (one per element)
    Each exam result is a dict with:
      - exam_type (str)
      - score (dict)
      - report (list of dicts with missed question details)
    """
    import collections
    import re
    import pdfplumber

    applicant_name = None
    exams = collections.defaultdict(lambda: {
        "exam_designator": None,
        "designators": [],
        "missed": [],
        "score": None
    })

    line_regex = re.compile(r'\d+\.\s+([TGE]\d[A-Z]\d{2}):\s+([A-D])(?:\s+\(should be\s+([A-D])\))?')
    score_regex = re.compile(r'Test (Passed|Failed)\s*-\s*(\d+)\s+out of\s+(\d+)', re.IGNORECASE)
    name_regex = re.compile(r'^([A-Za-z\'\- ]+)\s+\(PIN:\s*\d{4}\)', re.IGNORECASE)

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            score_match = None
            text = page.extract_text()
            if not text:
                continue

            for line in text.split('\n'):
                line = line.strip()

                # Extract applicant name (only from first page)
                if page_num == 0 and not applicant_name:
                    name_match = name_regex.match(line)
                    if name_match:
                        applicant_name = name_match.group(1).strip()

                # Extract score
                if not score_match:
                    score_match = score_regex.search(line)
                    if score_match:
                        status, correct_count, total = score_match.groups()
                        correct_count, total = int(correct_count), int(total)
                        exams[page_num]["score"] = {
                            "status": status.capitalize(),
                            "correct": correct_count,
                            "total": total,
                            "incorrect": total - correct_count
                        }

            # Process left and right columns
            width, height = page.width, page.height
            left_text = page.crop((0, 0, width / 2, height)).extract_text() or ''
            right_text = page.crop((width / 2, 0, width, height)).extract_text() or ''
            all_lines = (left_text + '\n' + right_text).split('\n')

            exam_designator = None
            for line in all_lines:
                line = line.strip()
                match = line_regex.search(line)
                if match:
                    designator, chosen, correct = match.groups()
                    if not exam_designator:
                        exam_designator = designator
                    correct = correct if correct else chosen
                    if chosen != correct:
                        exams[page_num]["missed"].append({
                            "designator": designator,
                            "chosen": chosen,
                            "correct": correct
                        })
                        exams[page_num]["designators"].append(designator)

            exams[page_num]["exam_designator"] = exam_designator

    # Post-process and sort results
    results = []
    for page_num in sorted(exams):
        exam = exams[page_num]
        if not exam["exam_designator"]:
            continue

        # Sort missed questions by designator
        exam["missed"].sort(key=lambda x: x['designator'])

        pool = load_question_pool(exam["exam_designator"])
        detailed_report = build_detailed_report(exam["missed"], pool)
        results.append({
            "exam_type": exam_type_from_designator(exam["exam_designator"]),
            "score": exam["score"],
            "report": detailed_report
        })

    return applicant_name, results

def exam_type_from_designator(designator):
    """
    Given a question designator like 'T6B02', return the exam type.

    Args:
        designator (str): The question designator (e.g., 'T1A01', 'G4B02', 'E1A05')

    Returns:
        str: 'Technician', 'General', 'Amateur Extra', or 'Unknown' if the prefix is not recognized.
    """
    exam_type_map = {
        'T': 'Technician',
        'G': 'General',
        'E': 'Amateur Extra'
    }
    return exam_type_map.get(designator[0].upper(), 'Unknown')

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