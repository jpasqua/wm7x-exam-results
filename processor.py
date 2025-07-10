import re
import pdfplumber
import json
import os

def parse_exam_pdf(pdf_path):
    missed_questions = []
    applicant_name = None

    line_regex = re.compile(r'\d+\.\s+([TGE]\d[A-D]\d{2}):\s+([A-D])(?:\s+\(should be\s+([A-D])\))?')
    name_regex = re.compile(r'^([A-Za-z\'\- ]+)\s+\(PIN:\s*\d{4}\)(?:\s+PASS)?$')

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            width = page.width
            height = page.height
            text = page.extract_text()

            if page_num == 0:
                for line in text.split('\n'):
                    name_match = name_regex.match(line.strip())
                    if name_match:
                        applicant_name = name_match.group(1).strip()
                        break

            left_bbox = (0, 0, width / 2, height)
            right_bbox = (width / 2, 0, width, height)

            left_text = page.crop(left_bbox).extract_text()
            right_text = page.crop(right_bbox).extract_text()

            all_lines = []
            if left_text:
                all_lines.extend(left_text.split('\n'))
            if right_text:
                all_lines.extend(right_text.split('\n'))

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

    missed_questions.sort(key=lambda x: x['designator'])
    return applicant_name, missed_questions

def load_question_pool(first_designator):
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

    return { q['id']: q for q in data }

def build_detailed_report(missed, question_pool):
    detailed_report = []
    for m in missed:
        q = question_pool.get(m['designator'])
        if not q:
            detailed_report.append({
                "designator": m['designator'],
                "question": "(Question text not found)",
                "your_answer_letter": m['chosen'],
                "your_answer_text": "(Unknown)",
                "correct_answer_letter": m['correct'],
                "correct_answer_text": "(Unknown)"
            })
            continue

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