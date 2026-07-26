import os
import json
import random
import sys
from typing import List, Dict, Optional
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


# Monkey-patch print to be Windows-console safe (cp1252 chokes on emoji).
# Replaces problematic chars with '?' instead of crashing.
_original_print = print
def print(*args, **kwargs):
    """Windows-safe print that replaces unprintable unicode chars."""
    try:
        _original_print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for a in args:
            if isinstance(a, str):
                safe_args.append(a.encode(sys.stdout.encoding or 'ascii', 'replace').decode(sys.stdout.encoding or 'ascii'))
            else:
                safe_args.append(a)
        _original_print(*safe_args, **kwargs)


def _safe_print(msg: str) -> None:
    """Print that won't crash on Windows console (cp1252) when msg has emoji."""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Fall back to ASCII-safe version
        ascii_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(ascii_msg)


class QuestionGenerator:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                _safe_print("✅ Question Generator initialized (GPT-4o-mini)")
                self.use_ai = True
            except Exception as e:
                _safe_print(f"⚠️  OpenAI API unavailable: {e}")
                self.client = None
                self.use_ai = False
        else:
            _safe_print("⚠️  OPENAI_API_KEY not found in environment")
            self.client = None
            self.use_ai = False

        self.template_questions = self._load_templates()

    def generate_questions_resume(self, profile: Dict, num_questions: int = 5) -> List[Dict]:
        """
        Generate personalized interview questions based on resume content.
        Field-agnostic: works for tech, business, engineering, design, etc.
        """
        username = profile.get('username', None)

        # Load question history for dedup
        recent_questions = self._load_question_history(username)

        # Extract resume context
        skills = profile.get('skills', [])
        projects = profile.get('projects', [])
        experience = profile.get('experience', [])
        field = profile.get('job_role', 'other')
        job_role = profile.get('job_role', 'Professional')
        difficulty = profile.get('difficulty', 'intermediate')
        interview_type = profile.get('interview_type', 'mixed')

        # Build context strings
        skills_text = ', '.join(skills[:15]) if skills else 'No skills extracted'

        projects_text = '\n'.join(
            f"- {p.get('name', 'Unknown')}: {p.get('description', 'No description')} (Methods/Tools: {', '.join(p.get('tech', []))})"
            for p in projects[:3]
        ) if projects else 'No projects extracted'

        experience_text = '\n'.join(
            f"- {e.get('role', 'Unknown')} at {e.get('company', 'Unknown')} ({e.get('duration', 'Unknown')}): {e.get('description', 'No description')}"
            for e in experience[:2]
        ) if experience else 'No experience extracted'

        # Exclusion text
        exclusion_text = ""
        if recent_questions:
            exclusion_text = f"\n\nAvoid these recently asked questions:\n" + '\n'.join(f"  - {q}" for q in recent_questions[:20])

        # Field-specific guidance
        field_guidance = {
            'technology': "Focus on technical depth, system design, coding, problem-solving.",
            'business':   "Focus on business impact, stakeholdnking, case scenarios.",
            'engineering':"Focus on engineering principles, design process, technical problem-solving, safety/standards.",
            'design':     "Focus on design process, user empathy, portfolio projects, creative problem-solving.",
            'sciences':   "Focus on research methodology, lab ing, data analysis.",
            'liberal_arts':"Focus on communication, critical thinking, research, writing, cultural awareness.",
            'healthcare': "Focus on patient care, clinical scenarios, ethics, teamwork, communication.",
            'education':  "Focus on pedagogy, classroom manageent engagement.",
            'other':      "Focus on general professional competencies relevant to the role."
        }.get(field, "Focus on general professional competencies.")

        if self.use_ai and self.client:
            try:
                prompt = f"""Generate {num_questions} personalized interview questions for a {job_role} position.

Candidate field: {field.upper()}
Field-specific focus: {field_guidance}

Candidate background (from their resume):
- Skills: {skills_text}

Projects/Work:
{projects_text}

Experience:
{experience_text}

Interview type: {interview_type}
Difficulty: {difficulty}
{exclusion_text}

Generate questions that:
1. Reference their SPECIFIC projects and experience (not generic)
2. Test skills they claim to have
3. Are appropriate for the {field} field
4. Feel personalized, not template-generated

Type rule: {interview_type.upper()}
- behavioral: STAR-format, past experiences
- technical: field-specific knowledge and methods
- mixed: alternate field-specific and behavioral

Return ONLY raw JSON array, no markdown, no code fences:
[
  {{
    "id": 1,
    "question": "specific personalized question",
    "category": "technical | behavioral | situational",
    "difficulty": "easy | medium | hard",
    "time_limit": 120
  }}
]"""

                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"You are an expert interviewer for {field} roles. Generate personalized questions based on the candidate's resume. Return only valid raw JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=1.0,
                    max_tokens=1500,
                    presence_penalty=0.6,
                    frequency_penalty=0.3
                )

                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]

                questions = json.loads(content.strip())
                print(f"✅ Generated {len(questions)} personalized questions for {field} field")
                print(f"🔧 DEBUG - self.use_ai: {self.use_ai}")
                print(f"🔧 DEBUG - job_role: {job_role}")
                print(f"🔧 DEBUG - field: {field}")
                # Save to history
                self._save_to_history(
                    username,
                    [q['question'] for q in questions],
                    interview_type,
                    job_role
                )

                return questions

            except Exception as e:
                print(f"⚠️  Resume-based generation failed: {e}")
                return self._generate_from_templates(profile,num_questions)
        else:
            return self._generate_from_templates(profile, num_questions)

    def _load_question_history(self, username: str = None) -> List[str]:
        try:
            from Backend.Utilities.database import db
            if username:
                return db.get_recent_questions(username, limit=30)
            return []
        except Exception as e:
            print(f"⚠️  Could not load question history: {e}")
            return []

    def _save_to_history(self, username: str = None, questions: List[str] = [], category: str = None, job_role: str = None):
        try:
            from Backend.Utilities.database import db
            if username and questions:
                db.save_questions(username, questions, category, job_role)
        except Exception as e:
            print(f"⚠️  Could not save question history: {e}")

    def _generate_with_openai(self, profile: Dict, num_questions: int, username: str = None) -> List[Dict]:
        interview_type = profile['interview_type'].lower() 
        job_role = profile.get('job_role', 'Professional')
        difficulty = profile['difficulty']  
        education_lvl = profile['education_lvl'] 
        degree = profile['degree'] 
        company_type = profile['company_type']

        recent_questions = self._load_question_history(username)
        random_seed = random.randint(1, 1000000)

        system_prompt = (
            f"You are a creative and experienced interviewer for {job_role} positions. "
            f"The Candidate has a education level of {education_lvl} {degree} degree and is interviewing for a {company_type}. "
            f"Generate UNIQUE, VARIED, and THOUGHTFUL questions. "
            f"The Candidate is a FRESHER with no prior work experience. "
            f"Avoid cliché or generic interview questions. "
            f"Avoid Asking questions regarding Professional Experience, as the candidate is a fresher. "
            f"Return only valid raw JSON — no markdown, no code fences, no explanation."
        )

        type_instructions = {
            'behavioral': (
                "Generate ONLY behavioral questions answerable in STAR format. but never mention STAR. "
                "Focus on: past experiences (dont ask if FRESHER), teamwork, conflict resolution, leadership "
                "handling failure, communication, adaptability, decision-making. "
                "Make each question UNIQUE — no repetitive themes. "
                "Do NOT include technical questions."
            ),
            'technical': (
                f"Generate ONLY technical questions specific to a {job_role} role. "
                f"Cover diverse topics: algorithms, design patterns, system design, "
                f"tools, frameworks, best practices, debugging, optimization. "
                f"Make each question UNIQUE and SPECIFIC — avoid generic questions. "
                f"Do NOT include soft-skill or behavioral questions."
            ),
            'mixed': (
                f"Generate EXACTLY {num_questions // 2} technical questions AND "
                f"EXACTLY {num_questions - num_questions // 2} behavioral questions. "
                f"Technical: diverse topics, {job_role}-specific, tests real knowledge. "
                f"Behavioral: STAR-format, varied scenarios, past experiences. "
                f"Make EVERY question unique and interesting. "
                f"Alternate them: technical, behavioral, technical, behavioral..."
            )
        }

        type_instruction = type_instructions.get(interview_type, type_instructions['mixed'])

        exclusion_text = ""
        if recent_questions:
            exclusion_text = f"""
DO NOT generate questions similar to these recently asked questions:
{chr(10).join(f"  ❌ {q}" for q in recent_questions)}

Make sure your questions are COMPLETELY DIFFERENT in topic, structure, and focus.
"""

        print(f"🤖 Generating {num_questions} UNIQUE [{interview_type}] questions...")

        prompt = f"""Generate exactly {num_questions} UNIQUE and CREATIVE interview questions.

Profile:
- Job Role:       {job_role}
- Degree:         {degree}
- Difficulty:     {difficulty}
- Company Type:   {company_type}
- Interview Type: {interview_type.upper()}

Type rule (STRICTLY follow):
{type_instruction}

Difficulty guide:
- beginner:     simple, common scenarios, foundational knowledge
- intermediate: requires real experience or solid understanding
- advanced:     deep expertise, complex scenarios, leadership thinking

{exclusion_text}

CRITICAL REQUIREMENTS:
1. Each question must be UNIQUE — no overlapping topics or themes
2. Avoid cliché questions like "tight deadlines" or "learning new technology fast"
3. Be SPECIFIC and CREATIVE — use real scenarios and concrete examples
4. Test different aspects of {job_role} work
5. Random seed for variety: {random_seed}

Return ONLY a raw JSON array. No markdown. No explanation. No code fences:
[
  {{
    "id": 1,
    "question": "specific and unique question text here",
    "category": "technical | behavioral | situational",
    "difficulty": "easy | medium | hard",
    "time_limit": 120
  }}
]"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt}
            ],
            temperature=1.1,
            max_tokens=1500,
            presence_penalty=0.6,
            frequency_penalty=0.3
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        questions = json.loads(content)
        print(f"✅ Generated {len(questions)} unique questions")
        return questions

    def _generate_from_templates(self, profile: Dict, num_questions: int) -> List[Dict]:
        print(f"📝 Generating {num_questions} questions from templates...")

        difficulty     = profile.get('difficulty',     'intermediate')
        interview_type = profile.get('interview_type', 'mixed').lower()

        difficulty_map = {
            'beginner':     ['easy'],
            'intermediate': ['easy', 'medium'],
            'advanced':     ['medium', 'hard'],
        }
        allowed = difficulty_map.get(difficulty.lower(), ['easy', 'medium'])

        if interview_type == 'technical':
            tech_pool = [q for q in self.template_questions['technical'] if q['difficulty'] in allowed]
            selected  = random.sample(tech_pool, min(num_questions, len(tech_pool)))
            while len(selected) < num_questions:
                selected.append(random.choice(tech_pool))
            print(f"✅ Selected {len(selected)} technical questions")

        elif interview_type == 'behavioral':
            behav_pool = [q for q in (self.template_questions['behavioral'] + self.template_questions['situational']) if q['difficulty'] in allowed]
            selected   = random.sample(behav_pool, min(num_questions, len(behav_pool)))
            while len(selected) < num_questions:
                selected.append(random.choice(behav_pool))
            print(f"✅ Selected {len(selected)} behavioral questions")

        elif interview_type == 'mixed':
            tech_pool  = [q for q in self.template_questions['technical']  if q['difficulty'] in allowed]
            behav_pool = [q for q in (self.template_questions['behavioral'] + self.template_questions['situational']) if q['difficulty'] in allowed]
            tech_count  = num_questions // 2
            behav_count = num_questions - tech_count
            tech_selected  = random.sample(tech_pool,  min(tech_count,  len(tech_pool)))
            behav_selected = random.sample(behav_pool, min(behav_count, len(behav_pool)))
            selected = tech_selected + behav_selected
            random.shuffle(selected)
            print(f"✅ Selected {len(tech_selected)} technical + {len(behav_selected)} behavioral = {len(selected)} total")

        else:
            all_questions = self.template_questions['technical'] + self.template_questions['behavioral'] + self.template_questions['situational']
            filtered  = [q for q in all_questions if q['difficulty'] in allowed]
            selected  = random.sample(filtered, min(num_questions, len(filtered)))

        for i, q in enumerate(selected, 1):
            q['id'] = i

        return selected

    def _load_templates(self) -> Dict:
        return {
            "technical": [
                {"question": "Explain the difference between a stack and a queue. When would you use each?",          "category": "technical",   "difficulty": "easy",   "time_limit": 120},
                {"question": "What is object-oriented programming? Explain the four pillars with examples.",           "category": "technical",   "difficulty": "easy",   "time_limit": 120},
                {"question": "How would you optimize a slow database query?",                                          "category": "technical",   "difficulty": "medium", "time_limit": 180},
                {"question": "Design a URL shortener like bit.ly. What components would you need?",                    "category": "technical",   "difficulty": "hard",   "time_limit": 240},
                {"question": "Explain REST APIs and how they differ from GraphQL.",                                    "category": "technical",   "difficulty": "medium", "time_limit": 120},
                {"question": "What is the time complexity of binary search and why?",                                  "category": "technical",   "difficulty": "easy",   "time_limit": 90},
                {"question": "Explain database indexing and when you would avoid using it.",                           "category": "technical",   "difficulty": "medium", "time_limit": 150},
                {"question": "How does garbage collection work in Python or Java?",                                    "category": "technical",   "difficulty": "medium", "time_limit": 120},
                {"question": "Design a system to handle 1 million concurrent users. Walk through your architecture.", "category": "technical",   "difficulty": "hard",   "time_limit": 300},
                {"question": "What is the difference between concurrency and parallelism?",                           "category": "technical",   "difficulty": "medium", "time_limit": 120},
            ],
            "behavioral": [
                {"question": "Tell me about a time you faced a challenging deadline. How did you handle it?",              "category": "behavioral", "difficulty": "easy",   "time_limit": 120},
                {"question": "Describe a situation where you had to work with a difficult team member.",                   "category": "behavioral", "difficulty": "medium", "time_limit": 120},
                {"question": "What's your greatest professional achievement and why?",                                     "category": "behavioral", "difficulty": "easy",   "time_limit": 120},
                {"question": "Tell me about a time you failed. What did you learn from it?",                               "category": "behavioral", "difficulty": "medium", "time_limit": 120},
                {"question": "How do you stay updated with new technologies in your field?",                               "category": "behavioral", "difficulty": "easy",   "time_limit": 90},
                {"question": "Describe a time you led a project without formal authority. How did you manage it?",         "category": "behavioral", "difficulty": "hard",   "time_limit": 150},
                {"question": "Tell me about a time you disagreed with your manager. What did you do?",                    "category": "behavioral", "difficulty": "medium", "time_limit": 120},
                {"question": "Give an example of when you had to learn something quickly under pressure.",                 "category": "behavioral", "difficulty": "medium", "time_limit": 120},
            ],
            "situational": [
                {"question": "If you discovered a critical bug in production, what steps would you take?",          "category": "situational", "difficulty": "medium", "time_limit": 120},
                {"question": "Your manager assigns you a task you strongly disagree with. How do you respond?",     "category": "situational", "difficulty": "medium", "time_limit": 120},
                {"question": "Two team members have conflicting implementation ideas. How would you mediate?",      "category": "situational", "difficulty": "hard",   "time_limit": 150},
                {"question": "You're running behind on a project deadline. What do you do?",                        "category": "situational", "difficulty": "easy",   "time_limit": 90},
                {"question": "You inherit a legacy codebase with no documentation. How do you approach it?",       "category": "situational", "difficulty": "medium", "time_limit": 120},
            ]
        }

def quick_generate(num_questions: int = 5, interview_type: str = 'mixed') -> List[Dict]:
    generator = QuestionGenerator()
    return generator.generate_questions(num_questions=num_questions, interview_type=interview_type)


if __name__ == "__main__":
    print("\n🎯 Testing Question Generator\n")
    generator = QuestionGenerator()

    for itype in ['behavioral', 'technical', 'mixed']:
        print(f"\n{'='*60}")
        print(f"Testing type: {itype.upper()}")
        print('='*60)
        profile = {
            "job_role":       "Software Engineer",
            "degree":         "Computer Science",
            "difficulty":     "intermediate",
            "company_type":   "Tech Company",
            "interview_type": itype
        }
        questions = generator.generate_questions(profile=profile, num_questions=6)
        for q in questions:
            print(f"{q['id']}. [{q['category'].upper()}] {q['question']}")
            print(f"   Difficulty: {q['difficulty']} | Time: {q['time_limit']}s\n")