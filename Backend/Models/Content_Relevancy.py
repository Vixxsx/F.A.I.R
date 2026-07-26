import os
import json
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


class ContentRelevancyAnalyzer:
    def __init__(self):

        self.api_key = os.getenv('OPENAI_API_KEY')

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.use_ai = True
                print("✅ Content Relevancy Analyzer initialized (GPT-4o-mini)")
            except Exception as e:
                print(f"⚠️  OpenAI unavailable for relevancy: {e}")
                self.client = None
                self.use_ai = False
        else:
            print("⚠️  OPENAI_API_KEY not found - using rule-based relevancy")
            self.client = None
            self.use_ai = False


    def analyze(self, question: str, answer: str, job_role: str = "Professional") -> Dict:
        """
        Main entry point. Analyze how relevant the answer is to the question.

        Returns:
        {
            "relevancy_score":   int (0-100),
            "relevancy_label":   str ("High" / "Medium" / "Low" / "Off-topic"),
            "cant_answer":       bool,
            "gibberish":         bool,
            "feedback":          str,
            "key_points_hit":    list[str],
            "key_points_missed": list[str],
            "suggestion":        str
        }
        """

        # Edge case: empty or very short answer
        if not answer or len(answer.strip()) < 10:
            return self._no_answer_result()

        # Detect "can't answer" phrases before hitting the API
        cant_answer = self._detect_cant_answer(answer)

        if self.use_ai and self.client:
            try:
                return self._analyze_with_openai(question, answer, job_role, cant_answer)
            except Exception as e:
                print(f"⚠️  OpenAI relevancy failed: {e}")
                return self._rule_based_fallback(question, answer, cant_answer)
        else:
            return self._rule_based_fallback(question, answer, cant_answer)


    def _analyze_with_openai(
        self,
        question: str,
        answer: str,
        job_role: str,
        cant_answer: bool
    ) -> Dict:

        print(f"🔍 Analyzing content relevancy with GPT-4o-mini...")

        # Give the model context about a can't-answer situation so it scores fairly
        cant_answer_note = (
            "NOTE: The candidate indicated they are unsure or cannot answer this question. "
            "Score their attempt fairly — partial credit if they tried to reason through it. "
            "Set 'cant_answer' to true in your response.\n\n"
            if cant_answer else ""
        )

        prompt = f"""You are an expert interview evaluator for a {job_role} position.

Evaluate how relevant and complete this interview answer is to the question asked.

Question:
\"\"\"{question}\"\"\"

Candidate's Answer:
\"\"\"{answer}\"\"\"

{cant_answer_note}
Evaluate on these dimensions:
1. Does the answer actually address what was asked?
2. Is the content relevant to the {job_role} role?
3. Are there specific examples or details, or is it vague?
4. Is the answer gibberish / incoherent / completely off-topic?
5. Does it show the candidate understands the question?

Return ONLY a raw JSON object. No markdown. No explanation:
{{
  "relevancy_score":   <integer 0-100>,
  "relevancy_label":   "<High | Medium | Low | Off-topic>",
  "cant_answer":       <true | false>,
  "gibberish":         <true | false>,
  "feedback":          "<2-3 sentence honest assessment of the answer quality>",
  "key_points_hit":    ["<point the candidate addressed well>", ...],
  "key_points_missed": ["<important point they should have mentioned>", ...],
  "suggestion":        "<one specific actionable tip to improve this answer>"
}}

IMPORTANT: Be LENIENT and FAIR. Many candidates are nervous.
Give credit for partial attempts and effort.

Scoring guide (BE LENIENT):
- 80-100: Directly addresses the question with good relevant detail
- 65-79:  Addresses the question with some relevant points, may lack depth  
- 50-64:  Attempts to answer, somewhat relevant but vague or incomplete
- 35-49:  Partially relevant or tangential, but shows some understanding
- 20-34:  Barely addresses the question, mostly off-topic
- 0-19:   Gibberish, completely irrelevant, or no real attempt

REMEMBER: Give credit for trying! Most answers should score 50-75. However Dont give credit for rambling off-topic or missing the point entirely."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a fair and encouraging interview evaluator for {job_role} roles. "
                        f"Be lenient - give credit for trying. Return only valid raw JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,   # Low temperature — we want consistent scoring
            max_tokens=600
        )

        content = response.choices[0].message.content.strip()

        # Strip markdown fences if model adds them anyway
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)

        # Ensure all keys exist with safe defaults
        result.setdefault("relevancy_score",   0)
        result.setdefault("relevancy_label",   "Low")
        result.setdefault("cant_answer",       cant_answer)
        result.setdefault("gibberish",         False)
        result.setdefault("feedback",          "No feedback available.")
        result.setdefault("key_points_hit",    [])
        result.setdefault("key_points_missed", [])
        result.setdefault("suggestion",        "Try to directly address the question asked.")

        print(f"✅ Relevancy score: {result['relevancy_score']}/100 ({result['relevancy_label']})")
        return result


    def _detect_cant_answer(self, answer: str) -> bool:
        """
        Detect if the candidate is signalling they can't or don't know how to answer.
        Checked before hitting the API so we can give the model the right context.
        """
        answer_lower = answer.lower().strip()

        cant_phrases = [
            "i don't know", "i dont know",
            "i'm not sure", "im not sure",
            "i have no idea", "no idea",
            "i can't answer", "i cant answer",
            "i don't have", "i dont have",
            "not sure about", "i'm unsure",
            "i cannot answer", "i don't know how",
            "i have no experience", "never done this",
            "i haven't", "i have not",
            "i'm not familiar", "not familiar with",
            "i don't understand the question",
        ]

        return any(phrase in answer_lower for phrase in cant_phrases)


    def _rule_based_fallback(self, question: str, answer: str, cant_answer: bool) -> Dict:
        """
        Simple fallback when OpenAI is unavailable.
        Uses word overlap and length heuristics.
        """
        print("📝 Using rule-based relevancy fallback...")

        if cant_answer:
            return {
                "relevancy_score":   20,
                "relevancy_label":   "Low",
                "cant_answer":       True,
                "gibberish":         False,
                "feedback":          "You indicated you couldn't answer this question. That's okay — try to reason through what you do know next time.",
                "key_points_hit":    [],
                "key_points_missed": ["Direct answer to the question"],
                "suggestion":        "Even if unsure, try to structure a partial answer using what you do know."
            }

        answer_words = set(answer.lower().split())
        question_words = set(question.lower().split()) - {
            "the","a","an","is","are","was","were","how","what",
            "why","when","where","who","would","could","should","did",
            "do","does","have","has","had","you","your","me","my","i"
        }

        # Word overlap ratio
        overlap = len(answer_words & question_words)
        overlap_ratio = overlap / max(len(question_words), 1)

        # Length score — very short answers are penalized
        word_count = len(answer.split())
        if word_count < 20:
            length_score = 30
        elif word_count < 50:
            length_score = 60
        elif word_count < 200:
            length_score = 90
        else:
            length_score = 80

        # Combine
        score = int((overlap_ratio * 50) + (length_score * 0.5))
        score = max(0, min(score, 100))

        if score >= 70:
            label = "High"
        elif score >= 45:
            label = "Medium"
        elif score >= 20:
            label = "Low"
        else:
            label = "Off-topic"

        return {
            "relevancy_score":   score,
            "relevancy_label":   label,
            "cant_answer":       False,
            "gibberish":         word_count < 5,
            "feedback":          f"Answer scored {score}/100 based on relevancy to the question.",
            "key_points_hit":    [],
            "key_points_missed": [],
            "suggestion":        "Make sure your answer directly addresses what was asked."
        }


    def _no_answer_result(self) -> Dict:
        """Return when answer is empty or too short to evaluate."""
        return {
            "relevancy_score":   0,
            "relevancy_label":   "Off-topic",
            "cant_answer":       True,
            "gibberish":         False,
            "feedback":          "No answer was provided.",
            "key_points_hit":    [],
            "key_points_missed": ["Complete answer to the question"],
            "suggestion":        "Always attempt an answer — even a partial attempt shows effort."
        }


    def batch_analyze(self, qa_pairs: list, job_role: str = "Professional") -> Dict:
        """
        Analyze multiple question-answer pairs and return an aggregate summary.

        qa_pairs: [{"question": "...", "answer": "..."}, ...]
        """
        results = []

        for i, pair in enumerate(qa_pairs):
            print(f"\n📊 Analyzing Q{i+1}/{len(qa_pairs)}...")
            result = self.analyze(
                question=pair.get("question", ""),
                answer=pair.get("answer", ""),
                job_role=job_role
            )
            result["question_index"] = i + 1
            results.append(result)

        # Aggregate
        scores          = [r["relevancy_score"]   for r in results]
        avg_score       = round(sum(scores) / len(scores), 1) if scores else 0
        cant_answer_count = sum(1 for r in results if r["cant_answer"])
        gibberish_count   = sum(1 for r in results if r["gibberish"])

        high_count   = sum(1 for r in results if r["relevancy_label"] == "High")
        medium_count = sum(1 for r in results if r["relevancy_label"] == "Medium")
        low_count    = sum(1 for r in results if r["relevancy_label"] in ["Low", "Off-topic"])

        if avg_score >= 75:
            overall_label = "Strong"
        elif avg_score >= 50:
            overall_label = "Moderate"
        else:
            overall_label = "Needs Improvement"

        return {
            "individual_results":   results,
            "summary": {
                "average_score":        avg_score,
                "overall_label":        overall_label,
                "total_questions":      len(results),
                "high_relevancy":       high_count,
                "medium_relevancy":     medium_count,
                "low_relevancy":        low_count,
                "couldnt_answer":       cant_answer_count,
                "gibberish_detected":   gibberish_count,
            }
        }


# ========== TEST ==========

if __name__ == "__main__":
    analyzer = ContentRelevancyAnalyzer()

    tests = [
        {
            "label": "Good relevant answer",
            "question": "Tell me about a time you handled a tight deadline.",
            "answer": "In my previous job, we had a product launch coming up and our team was behind schedule. I prioritized the critical features, delegated tasks based on strengths, and we worked extra hours that week. We shipped on time and the client was happy.",
        },
        {
            "label": "Vague answer",
            "question": "Explain how you would optimize a slow database query.",
            "answer": "I would just make it faster by checking the database and fixing things.",
        },
        {
            "label": "Can't answer",
            "question": "Describe your experience with Kubernetes deployment pipelines.",
            "answer": "I'm not sure about this, I don't have experience with Kubernetes specifically.",
        },
        {
            "label": "Completely off-topic",
            "question": "How do you handle conflict with a team member?",
            "answer": "I really enjoy cooking pasta and watching football on weekends.",
        },
    ]

    for test in tests:
        print(f"\n{'='*60}")
        print(f"Test: {test['label']}")
        print(f"Q: {test['question']}")
        print(f"A: {test['answer']}")
        print(f"{'='*60}")

        result = analyzer.analyze(
            question=test["question"],
            answer=test["answer"],
            job_role="Software Engineer"
        )

        print(f"Score:      {result['relevancy_score']}/100")
        print(f"Label:      {result['relevancy_label']}")
        print(f"Can't ans:  {result['cant_answer']}")
        print(f"Gibberish:  {result['gibberish']}")
        print(f"Feedback:   {result['feedback']}")
        print(f"Suggestion: {result['suggestion']}")