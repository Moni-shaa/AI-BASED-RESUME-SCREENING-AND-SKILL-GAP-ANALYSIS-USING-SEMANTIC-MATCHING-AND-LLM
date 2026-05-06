import os
import requests
import json
import re
from dotenv import load_dotenv

# Load environment variables from the backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(backend_dir, '.env'))

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        if not self.api_key:
            print("⚠️  WARNING: GEMINI_API_KEY not found in environment variables")
            self.configured = False
        else:
            print("✅ Gemini API configured successfully")
            print(f"   API Key: {self.api_key[:20]}...")
            print(f"   Endpoint: {self.endpoint}")
            self.configured = True

    def _call_gemini(self, messages, temperature=0.7, max_tokens=1024):
        """Call Google Gemini API with proper structure"""
        if not self.configured:
            return self._get_mock_response()

        try:
            # Separate system prompt and chat history
            system_instruction = None
            contents = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    if system_instruction is None:
                        system_instruction = {"parts": [{"text": msg['content']}]}
                    else:
                        # Append to existing system instruction
                        system_instruction["parts"][0]["text"] += "\n\n" + msg['content']
                elif msg['role'] == 'user':
                    contents.append({
                        "role": "user",
                        "parts": [{"text": msg['content']}]
                    })
                elif msg['role'] == 'model' or msg['role'] == 'assistant':
                    contents.append({
                        "role": "model",
                        "parts": [{"text": msg['content']}]
                    })

            # If no contents (e.g. only system prompt), add a dummy user message or handle it
            # But usually there is a user prompt.
            if not contents:
                # Fallback if only system prompt was provided (unlikely in this app)
                 contents.append({
                        "role": "user",
                        "parts": [{"text": "Please proceed."}]
                    })

            url = f"{self.endpoint}?key={self.api_key}"

            headers = {
                'Content-Type': 'application/json'
            }

            data = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "response_mime_type": "application/json"
                }
            }
            
            if system_instruction:
                data["systemInstruction"] = system_instruction

            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Gemini API Error {response.status_code}: {response.text}")
                response.raise_for_status()

            result = response.json()

            # Extract response text
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate.get("content", {}).get("parts", [])
                    text = "".join(p.get("text","") for p in parts)
                    return text

            return "Sorry, I couldn't process that request."

        except requests.exceptions.RequestException as e:
            print(f"❌ Gemini API request error: {e}")
            return self._get_mock_response()
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return self._get_mock_response()

    def _get_mock_response(self):
        return "I'm sorry, I cannot process your request right now because the AI service is unavailable. Please check your API key configuration."

    def skill_gap_analysis(self, resume_skills, jd_skills):

       resume_set = set([s.lower() for s in resume_skills])
       jd_set = set([s.lower() for s in jd_skills])

       matched = resume_set.intersection(jd_set)
       missing = jd_set - resume_set

       return {
        "matched_skills": list(matched),
        "missing_skills": list(missing),
        "match_percentage": round(len(matched) / len(jd_set) * 100, 2) if jd_set else 0
    }

    

    def analyze_resume(self, resume_text, job_description=""):
        """Analyze resume and provide comprehensive evaluation"""
        try:
            prompt = f"""
            Analyze the following resume and provide a comprehensive evaluation in JSON format.

            Resume Text:
            {resume_text}

            Job Description (if provided):
            {job_description}

            Please provide analysis in the following JSON structure:
            {{
                "overall_score": <number 0-100>,
                "category": "<Highly Qualified|Qualified|Not a Fit>",
                "summary": "<brief summary>",
                "strengths": ["<strength1>", "<strength2>", ...],
                "weaknesses": ["<weakness1>", "<weakness2>", ...],
                "skills_match": <number 0-100>,
                "experience_level": "<Junior|Mid-level|Senior|Expert>",
                "experience_years": <number>,
                "key_skills": ["<skill1>", "<skill2>", ...],
                "education": "<education details>",
                "recommendations": ["<recommendation1>", "<recommendation2>", ...],
                "red_flags": ["<flag1>", "<flag2>", ...],
                "contact_info": {{
                    "name": "<name>",
                    "email": "<email>",
                    "phone": "<phone>"
                }}
            }}

            Ensure the response is valid JSON only, no additional text.
            """

            messages = [
                {"role": "system", "content": "You are an expert HR professional and resume analyst. Provide detailed, objective analysis in valid JSON format only."},
                {"role": "user", "content": prompt}
            ]

            response = self._call_gemini(messages)

            # remove markdown formatting from Gemini
            response = response.replace("```json", "").replace("```", "").strip()

            try:
               json_match = re.search(r"\{.*\}", response, re.DOTALL)

               if json_match:
                  json_str = json_match.group()
                  analysis = json.loads(json_str)

                  # add skill gap analysis
                  resume_skills = analysis.get("key_skills", [])
                  jd_skills = self._extract_skills(job_description) if job_description else []

                  gap_analysis = self.skill_gap_analysis(resume_skills, jd_skills)

                  analysis["skill_gap"] = gap_analysis
                  analysis["strengths"] = [f"Strong experience in {s}" for s in gap_analysis["matched_skills"][:5]]
                  analysis["weaknesses"] = [f"Missing experience in {s}" for s in gap_analysis["missing_skills"][:5]]
                  return analysis
               else:
                    raise ValueError("No JSON found in Gemini response")
            except json.JSONDecodeError:
                print(f"❌ JSON parsing failed, using mock analysis. Response: {response[:200]}...")
                return self._get_mock_analysis(resume_text)

        except Exception as e:
            print(f"❌ Error in resume analysis: {str(e)}")
            return self._get_mock_analysis(resume_text)

    def _get_mock_analysis(self, resume_text=""):
        """Return mock analysis structure with unique data based on resume content"""
        import random
        import re
        import hashlib

        # Create a seed based on resume content for consistent but unique results
        content_hash = hashlib.md5(resume_text.encode()).hexdigest()
        random.seed(content_hash)

        # Extract actual information from resume text
        name = self._extract_name(resume_text)
        email = self._extract_email(resume_text)
        phone = self._extract_phone(resume_text)
        skills = self._extract_skills(resume_text)

        # simulate JD skills from resume skills list
        jd_skills = skills[:5] + ["AWS","TensorFlow","Pandas","PyTorch"]

        gap_analysis = self.skill_gap_analysis(skills, jd_skills)
        experience_years = self._estimate_experience(resume_text)
        education = self._extract_education(resume_text)

        # Generate varied scores based on content
        base_score = random.randint(60, 95)
        skills_match = random.randint(65, 90)

        # Determine category based on score
        if base_score >= 85:
            category = "Highly Qualified"
        elif base_score >= 70:
            category = "Qualified"
        else:
            category = "Not a Fit"

        # Determine experience level
        if experience_years >= 7:
            exp_level = "Senior"
        elif experience_years >= 4:
            exp_level = "Mid-level"
        elif experience_years >= 1:
            exp_level = "Junior"
        else:
            exp_level = "Entry-level"

        # Generate varied strengths and weaknesses
        matched = gap_analysis.get("matched_skills", [])
        missing = gap_analysis.get("missing_skills", [])

        strengths = []
        weaknesses = []

       # intelligent strengths
        for skill in matched:
           if skill.lower() in ["python","flask","machine learning","artificial intelligence"]:
              strengths.append(f"Strong experience in {skill} related development")

        # intelligent weaknesses
        for skill in missing:
            if skill.lower() == "aws":
                weaknesses.append("No hands-on experience with AWS cloud services")
            elif skill.lower() == "azure":
                weaknesses.append("No exposure to Microsoft Azure platform")
            elif skill.lower() == "rest api":
                weaknesses.append("Limited experience designing REST APIs")
            else:
                weaknesses.append(f"Missing experience in {skill}")
        # Generate recommendations
        recommendations = [
            "Consider for technical interview",
            "Assess problem-solving skills in coding challenge",
            "Evaluate cultural fit",
            "Check references from previous employers",
            "Discuss career goals and growth plans"
        ]
        selected_recommendations = random.sample(recommendations, random.randint(2, 4))
        top_strengths = ", ".join(matched[:3]) if matched else ", ".join(skills[:3])

        return {
            "overall_score": base_score,
            "category": category,
            "strengths": strengths,

            "summary": f"{exp_level} candidate with {experience_years} years of experience. Strong skills in {top_strengths}.",
            "weaknesses": weaknesses,
            "skills_match": skills_match,
            "experience_level": exp_level,
            "experience_years": experience_years,
            "key_skills": skills,
            "skill_gap": gap_analysis,
            "education": education,
            "recommendations": selected_recommendations,
            "red_flags": [],
            "contact_info": {
                "name": name,
                "email": email,
                "phone": phone
            }
        }

    def _extract_name(self, text):
        """Extract name from resume text using enhanced parser"""
        from services.resume_parser import ResumeParser

        parser = ResumeParser()
        contact_info = parser.extract_contact_info(text)

        return contact_info.get('name', 'Candidate Name')

    def _extract_email(self, text):
        """Extract email from resume text using enhanced parser"""
        from services.resume_parser import ResumeParser

        parser = ResumeParser()
        contact_info = parser.extract_contact_info(text)

        return contact_info.get('email', 'candidate@email.com')

    def _extract_phone(self, text):
        """Extract phone number from resume text using enhanced parser"""
        from services.resume_parser import ResumeParser

        parser = ResumeParser()
        contact_info = parser.extract_contact_info(text)

        return contact_info.get('phone', '+1-234-567-8900')

    def _extract_skills(self, text):
        """Extract skills from resume text using enhanced parser"""
        from services.resume_parser import ResumeParser

        parser = ResumeParser()
        skills = parser.extract_skills(text)

        # If no skills found, generate some based on content
        if not skills:
            import random
            random.seed(hash(text) % 1000)
            default_skills = ["Python", "JavaScript", "SQL", "Git", "Communication"]
            skills = random.sample(default_skills, random.randint(3, 5))

        return skills[:10]  # Limit to 10 skills

    def _estimate_experience(self, text):
        """Estimate years of experience from resume text using enhanced parser"""
        from services.resume_parser import ResumeParser

        parser = ResumeParser()
        experience = parser.extract_experience_years(text)

        # If no experience found, make a reasonable estimate
        if experience == 0:
            import random
            random.seed(hash(text) % 1000)
            experience = random.randint(1, 5)

        return experience

    def _extract_education(self, text):
        """Extract education information from resume text using enhanced parser"""
        from services.resume_parser import ResumeParser

        parser = ResumeParser()
        education_list = parser.extract_education(text)

        if education_list and education_list[0] != "Education information not clearly specified":
            return "; ".join(education_list[:2])  # Join first 2 education entries

        # Default education based on content analysis
        text_lower = text.lower()
        if "computer" in text_lower or "software" in text_lower or "programming" in text_lower:
            return "Bachelor's degree in Computer Science"
        elif "business" in text_lower or "management" in text_lower:
            return "Bachelor's degree in Business Administration"
        elif "engineering" in text_lower:
            return "Bachelor's degree in Engineering"
        else:
            return "Bachelor's degree"

    def chat_about_candidate(self, candidate, message):
        """Chat about a specific candidate with enhanced formatting"""
        try:
            # Extract key candidate information
            analysis = candidate.get('analysis', {})
            contact_info = analysis.get('contact_info', {})
            name = contact_info.get('name', 'This candidate')
            score = analysis.get('overall_score', 0)
            category = analysis.get('category', 'Unknown')
            skills = analysis.get('key_skills', [])
            experience = analysis.get('experience_years', 0)
            strengths = analysis.get('strengths', [])
            weaknesses = analysis.get('weaknesses', [])

            candidate_summary = f"""
**Candidate Profile:**
- **Name:** {name}
- **Overall Score:** {score}%
- **Category:** {category}
- **Experience:** {experience} years
- **Key Skills:** {', '.join(skills[:5])}
- **Top Strengths:** {', '.join(strengths[:3])}
- **Areas for Improvement:** {', '.join(weaknesses[:2])}
"""

            prompt = f"""
            You are an expert HR consultant providing detailed insights about a specific candidate.

            {candidate_summary}

            User Question: {message}

            RESPONSE FORMATTING REQUIREMENTS:
            - Provide structured, well-formatted responses
            - Use bullet points and numbered lists where appropriate
            - Include specific examples from the candidate's profile
            - Use **bold** for emphasis on key points
            - Be specific and actionable in your recommendations
            - Reference the candidate by name when possible
            - Provide concrete insights based on their skills and experience

            Please provide a detailed, professional response about this candidate.
            """

            messages = [
                {"role": "system", "content": """You are an expert HR consultant with deep expertise in candidate evaluation, talent assessment, and recruitment strategy.

RESPONSE FORMATTING RULES:
- Always provide structured, well-formatted responses
- Use **bold** for candidate names and key points
- Use bullet points for lists and recommendations
- Include specific scores, skills, and qualifications
- Provide actionable insights and recommendations
- Reference specific candidate data in your responses
- Be professional but conversational
- Format responses for easy reading and scanning"""},
                {"role": "user", "content": prompt}
            ]

            return self._call_gemini(messages)

        except Exception as e:
            print(f"❌ API call failed for candidate chat, using mock response: {e}")
            return self._generate_mock_candidate_response(candidate, message)

    def _generate_mock_candidate_response(self, candidate, message):
        """Generate mock response for candidate chat when API fails"""
        analysis = candidate.get('analysis', {})
        name = analysis.get('contact_info', {}).get('name', 'This candidate')
        score = analysis.get('overall_score', 0)
        category = analysis.get('category', 'Unknown')

        if 'experience' in message.lower():
            return f"**{name}** has {analysis.get('experience_years', 0)} years of experience and is categorized as **{category}** with an overall score of {score}%."
        elif 'skills' in message.lower():
            skills = analysis.get('key_skills', [])
            return f"**{name}**'s key skills include: {', '.join(skills[:5])}. They have a skills match score of {analysis.get('skills_match', 0)}%."
        elif 'strengths' in message.lower():
            strengths = analysis.get('strengths', [])
            return f"**{name}**'s main strengths are: {', '.join(strengths[:3])}."
        else:
            return f"**{name}** is a **{category}** candidate with an overall score of {score}%. They have {analysis.get('experience_years', 0)} years of experience and strong skills in {', '.join(analysis.get('key_skills', [])[:3])}."

    def hr_assistant_chat(self, candidates, message):
        """General HR assistant chat about all candidates"""
        try:
            print(f"🔄 HR Assistant Chat - Message: {message}")
            print(f"🔄 HR Assistant Chat - Candidates count: {len(candidates) if candidates else 0}")

            # Summarize candidates for context
            candidate_summary = []
            if candidates:
                for candidate in candidates[:10]:  # Limit to first 10 candidates
                    try:
                        summary = {
                            "id": candidate.get("id", "unknown"),
                            "name": candidate.get("analysis", {}).get("contact_info", {}).get("name", "Unknown"),
                            "category": candidate.get("analysis", {}).get("category", "Unknown"),
                            "score": candidate.get("analysis", {}).get("overall_score", 0),
                            "skills": candidate.get("analysis", {}).get("key_skills", [])
                        }
                        candidate_summary.append(summary)
                    except Exception as e:
                        print(f"❌ Error processing candidate: {e}")
                        continue

            try:
                candidates_info = json.dumps(candidate_summary, indent=2)
            except Exception as e:
                print(f"❌ Error serializing candidates: {e}")
                candidates_info = "No candidate data available"

            prompt = f"""
            You are an expert HR assistant helping with candidate evaluation. Here's a summary of current candidates:

            {candidates_info}

            User question: {message}

            IMPORTANT FORMATTING GUIDELINES:
            - When asked about "top candidates", provide a numbered list with names, scores, and brief summaries
            - Use clear formatting with bullet points and structured layout
            - Include specific candidate names and key details
            - Provide actionable insights and recommendations
            - Keep responses concise but informative
            - Use markdown-style formatting for better readability

            Please provide a well-structured response based on the candidate data.
            """

            messages = [
                {"role": "system", "content": """You are an expert HR assistant with deep knowledge in recruitment, candidate evaluation, and HR analytics.

RESPONSE FORMATTING RULES:
- Always provide structured, well-formatted responses
- Use numbered lists for rankings (e.g., top candidates)
- Include candidate names, scores, and key qualifications
- Provide brief but meaningful summaries
- Use clear headings and bullet points
- Be specific and actionable in recommendations
- Format responses for easy reading and scanning"""},
                {"role": "user", "content": prompt}
            ]

            return self._call_gemini(messages)

        except Exception as e:
            print(f"❌ HR Assistant Chat Error: {str(e)}")
            print(f"❌ Error Type: {type(e).__name__}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return self._generate_mock_hr_response(candidates, message)

    def generate_interview_questions(self, candidate, job_description=""):
      """Generate interview questions using Gemini"""
      try:
          analysis = candidate.get("analysis", {})

          skills = analysis.get("key_skills", [])
          experience = analysis.get("experience_years", 0)

          prompt = f"""
You are a senior technical recruiter.

Generate interview questions for a candidate.

Candidate Skills: {', '.join(skills)}
Experience: {experience} years

Return ONLY JSON in this format:

{{
"technical_questions":[
{{"question":"...", "expected_answer_points":"..."}},
{{"question":"...", "expected_answer_points":"..."}}
],
"behavioral_questions":[
{{"question":"...", "looking_for":"..."}}
],
"soft_skills_questions":[
{{"question":"...", "purpose":"..."}}
]
}}
"""
          messages = [
            {"role": "system", "content": "You generate interview questions."},
            {"role": "user", "content": prompt}
          ]

          response = self._call_gemini(messages)

          if not response:
            raise ValueError("Empty Gemini response")

          # remove markdown
          response = response.replace("```json", "").replace("```", "").strip()

          import re

          json_match = re.search(r"\{.*\}", response, re.DOTALL)

          if json_match:
            json_text = json_match.group()
            return json.loads(json_text)

          raise ValueError("JSON not found")

      except Exception as e:
        print("❌ Gemini interview generation failed:", e)

        # fallback questions
        return {
            "technical_questions": [
                {
                    "question": "Explain a project you built using your main skill.",
                    "expected_answer_points": "Architecture, tools used, challenges solved"
                },
                {
                    "question": "How do you debug a complex technical issue?",
                    "expected_answer_points": "Logical troubleshooting steps"
                }
            ],
            "behavioral_questions": [
                {
                    "question": "Tell me about a challenging project you worked on.",
                    "looking_for": "Problem solving and teamwork"
                }
            ],
            "soft_skills_questions": [
                {
                    "question": "How do you handle conflicts in a team?",
                    "purpose": "Evaluate communication and collaboration"
                }
            ]
        }

    def compare_candidates(self, candidates, job_description=""):
        """Compare multiple candidates against a job description"""
        try:
            candidates_data = []
            for c in candidates:
                analysis = c.get('analysis', {})
                skills = analysis.get("key_skills", [])
                candidates_data.append({
                    "name": analysis.get('contact_info', {}).get('name', 'Unknown'),
                    "score": analysis.get('overall_score', 0),
                    "skills": analysis.get('key_skills', []),
                    
                    "experience": analysis.get('experience_years', 0)
                })
                
            prompt = f"""
You are an expert technical interviewer.

Generate interview questions based on this candidate profile.

Candidate Skills: {', '.join(skills)}


IMPORTANT:
Return ONLY valid JSON.
Do NOT add explanations.
Do NOT add markdown.

Example output:

{{
"technical_questions":[
{{"question":"Explain Python decorators","expected_answer_points":"Functions that wrap other functions"}},
{{"question":"What is REST API","expected_answer_points":"Stateless HTTP architecture"}}
],
"behavioral_questions":[
{{"question":"Tell me about a difficult project you handled","looking_for":"Problem solving and teamwork"}}
],
"soft_skills_questions":[
{{"question":"How do you resolve team conflict","purpose":"Communication and collaboration"}}
]
}}
"""
            
            messages = [
                {"role": "system", "content": "You are a hiring manager making a final decision. specific and decisive."},
                {"role": "user", "content": prompt}
            ]
            
            return self._call_gemini(messages)
            
        except Exception as e:
            print(f"❌ Error comparing candidates: {e}")
            return "Unable to compare candidates at this time."

    def _generate_mock_hr_response(self, candidates, message):
        """Generate mock response for HR chat when API fails"""
        if not candidates:
            return "I don't have any candidate data to work with. Please upload some resumes first."

        # Sort candidates by score
        sorted_candidates = sorted(candidates, key=lambda x: x.get('analysis', {}).get('overall_score', 0), reverse=True)

        if 'top' in message.lower() or 'best' in message.lower():
            response = "**Top Candidates:**\n\n"
            for i, candidate in enumerate(sorted_candidates[:5], 1):
                analysis = candidate.get('analysis', {})
                name = analysis.get('contact_info', {}).get('name', 'Unknown')
                score = analysis.get('overall_score', 0)
                category = analysis.get('category', 'Unknown')
                skills = analysis.get('key_skills', [])[:3]

                response += f"{i}. **{name}** - {score}% ({category})\n"
                response += f"   Skills: {', '.join(skills)}\n\n"

            return response

        elif 'statistics' in message.lower() or 'stats' in message.lower():
            total = len(candidates)
            qualified = len([c for c in candidates if c.get('analysis', {}).get('category') == 'Qualified'])
            highly_qualified = len([c for c in candidates if c.get('analysis', {}).get('category') == 'Highly Qualified'])

            return f"**Candidate Statistics:**\n\n- Total Candidates: {total}\n- Highly Qualified: {highly_qualified}\n- Qualified: {qualified}\n- Average Score: {sum(c.get('analysis', {}).get('overall_score', 0) for c in candidates) / total:.1f}%"

        else:
            return f"I have {len(candidates)} candidates in the system. The top performer is {sorted_candidates[0].get('analysis', {}).get('contact_info', {}).get('name', 'Unknown')} with a score of {sorted_candidates[0].get('analysis', {}).get('overall_score', 0)}%. Ask me about top candidates or statistics for more details."
