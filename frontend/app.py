from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

from services.resume_parser import ResumeParser
from services.gemini_service import GeminiService
from services.bias_detection import BiasDetector
from services.database import DatabaseManager
from services.email_service import EmailService
from services.resume_parser import ( calculate_weighted_match, decide_shortlist,calculate_semantic_similarity)
app = Flask(__name__)
CORS(app)

db_manager = DatabaseManager()
db_manager.init_db()

PRIORITY_KEYWORDS = {
    "high": ["must", "mandatory", "required", "strong", "essential"],
    "medium": ["preferred", "should have", "good knowledge"],
    "low": ["plus", "nice to have", "bonus"]
}

WEIGHTS = {
    "high_priority": 10,
    "medium_priority": 5,
    "low_priority": 2
}

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize services
resume_parser = ResumeParser()
ai_service = GeminiService()
bias_detector = BiasDetector()
email_service = EmailService()
gemini_service = GeminiService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ✅ PASTE STEP 2 HERE
def classify_skill_priority(jd_text, extracted_skills):
    jd_lower = jd_text.lower()

    priority_map = {
        "high_priority": [],
        "medium_priority": [],
        "low_priority": []
    }

    for skill in extracted_skills:
        assigned = False

        for word in PRIORITY_KEYWORDS["high"]:
            if word in jd_lower:
                priority_map["high_priority"].append(skill)
                assigned = True
                break

        if assigned:
            continue

        for word in PRIORITY_KEYWORDS["medium"]:
            if word in jd_lower:
                priority_map["medium_priority"].append(skill)
                assigned = True
                break

        if assigned:
            continue

        priority_map["low_priority"].append(skill)

    return priority_map


def calculate_weighted_score(priority_map, resume_skills):
    total_weight = 0
    matched_weight = 0

    breakdown = {
        "matched": [],
        "missing_high": [],
        "missing_medium": []
    }

    for category, skills in priority_map.items():
        weight = WEIGHTS[category]

        for skill in skills:
            total_weight += weight

            if skill in resume_skills:
                matched_weight += weight
                breakdown["matched"].append(skill)
            else:
                if category == "high_priority":
                    breakdown["missing_high"].append(skill)
                elif category == "medium_priority":
                    breakdown["missing_medium"].append(skill)

    score = (matched_weight / total_weight) * 100 if total_weight else 0

    return round(score, 2), breakdown

# -----------------------------------
# HEALTH CHECK
# -----------------------------------
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# -----------------------------------
# UPLOAD + ANALYZE
# -----------------------------------
@app.route('/api/upload', methods=['POST'])
def upload_resume():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['file']
        job_description = request.form.get('job_description', '')
        jd_file = request.files.get('jd_file')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF and DOCX allowed'}), 400

        # -----------------------------------
        # HANDLE JD (TEXT OR FILE)
        # -----------------------------------
        if jd_file and jd_file.filename != '':
            if not allowed_file(jd_file.filename):
                return jsonify({'error': 'Invalid JD file type'}), 400
            
            jd_filename = secure_filename(jd_file.filename)
            jd_unique_name = f"{uuid.uuid4()}_{jd_filename}"
            jd_path = os.path.join(app.config['UPLOAD_FOLDER'], jd_unique_name)
            jd_file.save(jd_path)

            job_description = resume_parser.extract_text(jd_path)

        # -----------------------------------
        # SAVE RESUME
        # -----------------------------------
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # -----------------------------------
        # PARSE RESUME
        # -----------------------------------
        resume_text = resume_parser.extract_text(file_path)

        # -----------------------------------
        # SKILL EXTRACTION
        # -----------------------------------
        resume_skills = resume_parser.extract_skills(resume_text)

        jd_skills = []
        if job_description:
            jd_skills = resume_parser.extract_skills(job_description)

        # -----------------------------------
        # SKILL GAP ANALYSIS
        # -----------------------------------
        matched_skills = list(set(resume_skills) & set(jd_skills))
        missing_skills = list(set(jd_skills) - set(resume_skills))

        priority_map = classify_skill_priority(job_description, jd_skills)

        weighted_score, score_details = calculate_weighted_score(
        priority_map,
        resume_skills
        )
        # -----------------------------------
        # SEMANTIC MATCHING (NEW)
        # -----------------------------------
        semantic_score = 0

        if job_description:
           semantic_score = calculate_semantic_similarity(
              resume_text,
              job_description
            )

        # Hybrid Final Score (50% semantic + 50% weighted)
        final_score = round(
            (0.6 * semantic_score) + (0.5 * weighted_score),
            2
        )
        print("\n===== CANDIDATE RESULT =====")
        print("Filename:", filename)
        print("Semantic Score:", semantic_score)
        print("Skill Score:", weighted_score)
        print("Final Score:", final_score)
        print("============================\n")   

        shortlisted = final_score >= 65

        matched = score_details["matched"]
        missing_high = score_details["missing_high"]
        missing_medium = score_details["missing_medium"]

        if shortlisted:

             decision_reason = f"""
<b>Score Summary</b>
• Skill Match Score: {weighted_score:.2f}%
• Semantic Similarity: {semantic_score:.2f}%
• Final Score: {final_score:.1f}%

<b>Score Calculation</b>
• Final Score = (0.5 × Semantic Similarity) + (0.5 × Skill Match)
• Final Score = (0.5 × {semantic_score:.2f}) + (0.5 × {weighted_score:.2f})

<b>Strengths</b>
• {matched[0] if len(matched) > 0 else "Skill Match"}
• {matched[1] if len(matched) > 1 else ""}
• {matched[2] if len(matched) > 2 else ""}

<b>Missing Critical Skills</b>
• {', '.join(missing_high) if missing_high else "None"}

<b>Hiring Decision</b>
Even though some critical skills like {', '.join(missing_high) if missing_high else "none"} are missing,  
the candidate demonstrates strong alignment with most required technologies.  
The final score meets the shortlist threshold, so the candidate is recommended for further evaluation.

<b>Recommendation</b>
• Improve expertise in missing technologies.
• Gain more experience in cloud or deployment tools.
"""

        else:

           decision_reason = f"""
<b>Score Summary</b>
• Skill Match Score: {weighted_score:.2f}%
• Semantic Similarity: {semantic_score:.2f}%
• Final Score: {final_score:.1f}%

<b>Score Calculation</b>
• Final Score = (0.5 × Semantic Similarity) + (0.5 × Skill Match)

<b>Strengths</b>
• {matched[0] if len(matched) > 0 else "Limited matching skills"}

<b>Missing Critical Skills</b>
• {', '.join(missing_high) if missing_high else "Multiple required skills missing"}

<b>Hiring Decision</b>
The candidate does not meet the shortlist threshold because several high-priority skills are missing.

<b>Recommendation</b>
• Develop the missing critical skills.
• Align more closely with the job requirements.
"""
        # -----------------------------------
        # AI ANALYSIS (Feedback only)
        # -----------------------------------
        analysis = ai_service.analyze_resume(resume_text, job_description)

        # -----------------------------------
        # SAVE TO DATABASE
        # -----------------------------------
        candidate_id = db_manager.save_candidate({
    'filename': filename,
    'file_path': file_path,
    'resume_text': resume_text,
    'job_description': job_description,
    'analysis': analysis,

    'skills': resume_skills,
    'jd_skills': jd_skills,

    'matched_skills': score_details["matched"],
    'missing_skills': missing_skills,
    'match_score': weighted_score,
    'semantic_score': semantic_score,   
    'final_score': final_score,  

    'priority_map': priority_map,
    'score_breakdown': score_details,
    'decision_reason': decision_reason,

    'shortlisted': shortlisted,

    'upload_date': datetime.now().isoformat()
})
        # -----------------------------------
        # RESPONSE
        # -----------------------------------
        return jsonify({
             'success': True,
             'candidate_id': candidate_id,
             'analysis': analysis,

             'resume_skills': resume_skills,
             'jd_skills': jd_skills,

             'matched_skills': score_details["matched"], 
             'missing_skills': score_details["missing_high"] + score_details["missing_medium"], 
             'match_score': weighted_score,
             'semantic_score': semantic_score,
             'final_score': final_score,
             'shortlisted': shortlisted,
             'decision_reason': decision_reason,

             'score_breakdown': score_details,
             'priority_map': priority_map,
             'category': "Qualified" if shortlisted else "Not a Fit"
        })

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return jsonify({'error': str(e)}), 500 
    
    


# -----------------------------------
# GET CANDIDATES
# -----------------------------------
@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    try:
        candidates = db_manager.get_all_candidates()
        return jsonify({'candidates': candidates})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


# -----------------------------------
# GET SINGLE CANDIDATE
# -----------------------------------
@app.route('/api/candidates/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    try:
        candidate = db_manager.get_candidate(candidate_id)

        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404

        return jsonify({
            'candidate': candidate,

            # ✅ ADD THESE LINES
            'matched_skills': candidate.get('matched_skills', []),
            'missing_skills': candidate.get('missing_skills', []),
            'resume_skills': candidate.get('skills', []),
            'jd_skills': candidate.get('jd_skills', []),
            'semantic_score': candidate.get('semantic_score'),
            'final_score': candidate.get('final_score'),
            'match_score': candidate.get('match_score')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interview-questions/<int:candidate_id>', methods=['GET'])
def get_interview_questions(candidate_id):
    try:
        candidate = db_manager.get_candidate(candidate_id)
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        questions = ai_service.generate_interview_questions(candidate, candidate.get('job_description', ''))
        return jsonify(questions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare-candidates', methods=['POST'])
def compare_candidates_endpoint():
    try:
        data = request.get_json()
        candidate_ids = data.get('candidate_ids', [])
        job_description = data.get('job_description', '')
        
        candidates = []
        for cid in candidate_ids:
            c = db_manager.get_candidate(cid)
            if c:
                candidates.append(c)
        
        if not candidates:
            return jsonify({'error': 'No valid candidates found'}), 400
            
        comparison = ai_service.compare_candidates(candidates, job_description)
        return jsonify({'comparison': comparison})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# -----------------------------------
# RUN APP
# -----------------------------------
if __name__ == '__main__':
    db_manager.init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)