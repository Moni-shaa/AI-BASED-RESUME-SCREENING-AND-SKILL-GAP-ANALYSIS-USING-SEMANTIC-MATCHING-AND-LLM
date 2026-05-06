from gpt4all import GPT4All

class LocalLLMService:

    def __init__(self):
        print("Loading local GPT4All model...")
        self.model = GPT4All("mistral-7b-instruct-v0.1.Q4_0.gguf")

    def chat(self, candidate, message):

        name = candidate.get("analysis", {}).get("contact_info", {}).get("name", "Candidate")
        skills = candidate.get("analysis", {}).get("key_skills", [])
        strengths = candidate.get("analysis", {}).get("strengths", [])
        experience = candidate.get("analysis", {}).get("experience_years", 0)

        context = f"""
Candidate Information

Name: {name}
Experience: {experience} years
Skills: {", ".join(skills)}
Strengths: {", ".join(strengths)}

Recruiter Question:
{message}
"""

        with self.model.chat_session():
            response = self.model.generate(context, max_tokens=200)

        return response