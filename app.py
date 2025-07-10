from flask import Flask, request, render_template
import os
import processor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

def exam_type_from_designator(designator):
    exam_map = {'T': 'Technician', 'G': 'General', 'E': 'Amateur Extra'}
    return exam_map.get(designator[0].upper(), 'Unknown')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('pdf_file')
        if not file or file.filename == '':
            return render_template('upload.html', error='No file selected.')

        if not file.filename.lower().endswith('.pdf'):
            return render_template('upload.html', error='Only PDF files are allowed.')

        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded.pdf')
        file.save(temp_path)

        try:
            applicant_name, missed = processor.parse_exam_pdf(temp_path)

            # Check: no applicant name AND no missed questions → invalid file
            if not applicant_name and not missed:
                return render_template(
                    'upload.html',
                    error="We could not extract any results from this file. Please make sure you are uploading an ExamTools 'Results' PDF."
                )

            # No missed questions but valid applicant → success message
            if not missed:
                exam_type = exam_type_from_designator('T')  # fallback if no designators present
                return render_template(
                    'report.html',
                    applicant=applicant_name,
                    exam_type=exam_type,
                    report=[],
                    message='No missed questions found.'
                )

            # Normal case: missed questions present
            exam_type = exam_type_from_designator(missed[0]['designator'])
            question_pool = processor.load_question_pool(missed[0]['designator'])
            detailed_report = processor.build_detailed_report(missed, question_pool)

            return render_template(
                'report.html',
                applicant=applicant_name,
                exam_type=exam_type,
                report=detailed_report
            )

        except Exception as e:
            print(f"[ERROR] Failed to process PDF: {e}")
            return render_template(
                'upload.html',
                error="We were not able to read the results. Please ensure that you have uploaded a valid 'Results' PDF from ExamTools."
            )

        finally:
            # Always try to delete the file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return render_template('upload.html')