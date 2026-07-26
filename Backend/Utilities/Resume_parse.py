from dotenv import load_dotenv,find_dotenv
import io
import os
import json
from openai import OpenAI
import re
import secrets
import hashlib
from typing import List, Dict, Tuple
import pdfplumber

class ResumeParser:
    SECTION_HEADERS = {
        "education": ['education','academic background','academic qualifications','qualifications'],
        "experience": ['experience','work experience','professional experience','work history','employment'],
        "projects": ['projects','personal projects','academic projects'],
        "skills": ['skills','technical skills','core competencies','expertise','techno'],
        "certifications": ['certifications','certificates','licenses','awards'],
    }
    FIELD_KEYWORDS = {
        'technology': {
            'languages':['python', 'java', 'javascript', 'typescript','c', 'c++', 'c#', 'ruby', 'go', 'rust', 'php', 'swift', 'kotlin', 'r','scala'],
            'frameworks':['react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'express', 'spring', 'rails', 'next.js', 'node.js', 'react native', 'flutter'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'dynamodb', 'sqlite', 'oracle', 'elasticsearch'],
            'ml_ai':['tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'opencv', 'nltk', 'huggingface', 'langchain'],
            'cloud':['aws', 'azure', 'gcp', 'google cloud', 'kubernetes', 'docker', 'terraform', 'jenkins', 'ansible'],
            'tools':['git', 'github', 'gitlab', 'jira', 'confluence', 'figma', 'postman', 'vscode', 'intellij'],
        },
        'business': {
            'analytics':  ['excel', 'powerpoint', 'word', 'tableau', 'power bi', 'sql', 'r', 'spss', 'sas', 'stata', 'vba', 'pivot tables'],
            'finance':    ['financial modeling', 'valuation', 'dcf', 'mergers', 'acquisitions', 'capital markets', 'equity research', 'bloomberg', 'factset', 'capital iq', 'gaap', 'ifrs'],
            'accounting': ['quickbooks', 'xero', 'sap', 'oracle financials', 'audit', 'tax', 'bookkeeping', 'accounts payable', 'accounts receivable', 'reconciliation'],
            'marketing':  ['seo', 'sem', 'ppc', 'google analytics', 'hubspot', 'salesforce', 'mailchimp', 'hootsuite', 'content marketing', 'social media', 'brand management', 'market research'],
            'consulting': ['case study', 'mckinsey', 'bcg', 'bain', 'deloitte', 'accenture', 'pwc', 'kpmg', 'strategy', 'operations consulting'],
            'sales':      ['salesforce', 'hubspot', 'crm', 'lead generation', 'b2b', 'b2c', 'enterprise sales', 'account management', 'cold calling'],
            'hr':         ['workday', 'bamboo hr', 'adp', 'recruitment', 'talent acquisition', 'onboarding', 'employee relations', 'compensation', 'benefits'],
            'operations': ['supply chain', 'logistics', 'procurement', 'inventory', 'lean', 'six sigma', 'kaizen', 'erp', 'sap', 'oracle'],
        },
        'engineering': {
            'mechanical': ['solidworks', 'autocad', 'catia', 'ansys', 'matlab', 'simulink', 'thermodynamics', 'fluid mechanics', 'manufacturing', 'cad', 'cam', 'fea', 'cfd'],
            'civil':      ['autocad', 'revit', 'staad pro', 'etabs', 'primavera', 'ms project', 'construction', 'structural', 'geotechnical', 'surveying'],
            'electrical': ['matlab', 'simulink', 'pspice', 'multisim', 'pcb design', 'altium', 'verilog', 'vhdl', 'embedd', 'microcontroller', 'fpga', 'signal processing'],
            'chemical':   ['aspen', 'hysys', 'matlab', 'chemcad', 'process simulation', 'reactor design', 'distillation', 'unit operations'],
        },
        'design': {
            'ux_ui':      ['figma', 'sketch', 'adobe xd', 'invision', 'prototyping', 'wireframing', 'user research', 'usability testing', 'design systems'],
            'graphic':    ['photoshop', 'illustrator', 'indesign', 'after effects', 'premiere', 'canva', 'typography', 'branding'],
            'product':    ['figma', 'user stories', 'roadmap', 'a/b testing', 'analytics', 'jira', 'confluence', 'product strategy'],
        },
        'sciences': {
            'biology':    ['pcr', 'gel electrophoresis', 'western blot', 'cell culture', 'microscopy', 'flow cytometry', 'elisa', 'genomics', 'bioinformatics'],
            'chemistry':  ['hplc', 'gc-ms', 'nmr', 'ftir', 'spectroscopy', 'titration', 'synthesis', 'analytical chemistry'],
            'physics':    ['matlab', 'mathematica', 'labview', 'particle physics', 'quantum', 'optics', 'simulation', 'data analysis'],
        },
        'liberal_arts': {
            'communications': ['public speaking', 'presentation', 'writing', 'editing', 'media relations', 'pr', 'journalism', 'content creation'],
            'english':     ['writing', 'editing', 'proofreading', 'literary analysis', 'research', 'publishing'],
            'history':     ['research', 'archival', 'historiography', 'writing', 'analysis', 'critical thinking'],
            'psychology':  ['research', 'statistics', 'spss', 'experiment design', 'clinical', 'counseling', 'cognitive'],
            'sociology':   ['research', 'statistics', 'qualitative', 'quantitative', 'ethnography', 'survey design'],
        },
        'healthcare': {
            'nursing':     ['patient care', 'clinical', 'epic', 'cerner', 'medication administration', 'iv', 'wound care', 'assessment'],
            'pre_med':     ['research', 'lab', 'mcat', 'clinical', 'volunteer', 'patient interaction'],
        },
        'education': {
            'teaching':    ['curriculum', 'lesson planning', 'classroom management', 'instructional design', 'edtech', 'assessment'],
        },        
    }

    UNFRIENDLY_MESSAGES = {
        'image_only':      'PDF appears to be scanned or image-only. ATS systems cannot read images. Please upload a text-based PDF.',
        'multi_column':    'Multi-column layout detected. ATS systems read left-to-right, top-to-bottom. Use a single-column layout.',
        'tables_detected': 'Tables detected. ATS systems often misparse table content. Use plain text formatting instead.',
        'too_short':       'Resume is too short (under 200 words). ATS systems expect detailed content. Add more details about your experience.',
        'too_long':        'Resume is too long (over 1500 words). Keep it to 1-2 pages for best results.',
        'no_email':        'No email address found. Include a professional email in your contact section.',
        'no_sections':     'No standard section headers found. Use clear headers like "Education", "Experience", "Skills", "Projects".',
        'special_chars':   'Excessive special characters detected. Stick to standard text and basic formatting.',
    }
    def parse(self,pdf_bytes: bytes, mask_personal: bool = False) -> Dict:
        try:
            ats_score,ats_issues,ats_warnings,raw_text=self._validate_ats(pdf_bytes)
            detected_field=self.detect_field(raw_text)
            extracted=self._extract_with_gpt(raw_text)
            extracted['field']=detected_field
            if mask_personal:
                extracted=self._mask_personal(extracted)
            is_ats_friendly=len(ats_issues)==0 and ats_score>=60
            return {
                'is_ats_friendly': is_ats_friendly,
                'ats_score': ats_score,
                'ats_issues': ats_issues,
                'ats_warnings': ats_warnings,
                'extracted': extracted,
                'field': detected_field,
                'masked': mask_personal,
                'raw_text': raw_text[:500] if raw_text else '',
            }
        except Exception as e:
            print(f"Resume parsing failed: {e}")
            return {
                'is_ats_friendly': False,
                'ats_score': 0,
                'ats_issues': [f'Parsing failed: {e}'],
                'ats_warnings': [],
                'extracted': None,
                'masked': mask_personal,
                'raw_text': '',
            }
    def _validate_ats(self,pdf_bytes: bytes) -> Tuple[int,List[str],List[str],str]:
        issues=[]
        warnings=[]
        score=100
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text=""
            for page in pdf.pages:
                page_text=page.extract_text() or ""
                full_text+=page_text+"\n"

                if not full_text.strip():
                    issues.append(self.UNFRIENDLY_MESSAGES['image_only'])
                    score-=30
                    break
                word_count=len(full_text.split())
                if word_count < 200:
                    issues.append(self.UNFRIENDLY_MESSAGES['too_short'])
                    score-=30
                elif word_count > 1500:
                    issues.append(self.UNFRIENDLY_MESSAGES['too_long'])
                    score-=10
                if not re.search(r'[\w.-]+@[\w.-]+\.\w+', full_text):
                    issues.append(self.UNFRIENDLY_MESSAGES['no_email'])
                    score -= 20
                text_lower = full_text.lower()
                section_count = 0
                for section, keywords in self.SECTION_HEADERS.items():
                    if any(kw in text_lower for kw in keywords):
                        section_count += 1

                if section_count < 2:
                    issues.append(self.UNFRIENDLY_MESSAGES['no_sections'])
                    score -= 25
                first_page = pdf.pages[0] if pdf.pages else None
                if first_page:
                    words = first_page.extract_words() or []
                    if words:
                        x_starts = [w['x0'] for w in words if w['x0'] < 100]  # Left margin words
                        unique_x_starts = len(set(round(x) for x in x_starts))
                        if unique_x_starts > 4:  # Multiple left-margin starting positions
                            warnings.append(self.UNFRIENDLY_MESSAGES['multi_column'])
                            score -= 10
                has_tables = False
                for page in pdf.pages:
                    if page.extract_tables():
                        has_tables = True
                        break
                if has_tables:
                    warnings.append(self.UNFRIENDLY_MESSAGES['tables_detected'])
                    score -= 10

                # Check 7: Special characters
                special_char_count = len(re.findall(r'[^\w\s.,;:()\-/]', full_text))
                special_ratio = special_char_count / max(len(full_text), 1)
                if special_ratio > 0.05:
                    warnings.append(self.UNFRIENDLY_MESSAGES['special_chars'])
                    score -= 5

            return max(0, score), issues, warnings, full_text
    def detect_field(self, text: str) -> str:
        text_lower = text.lower()
        field_scores = {}

        for field, categories in self.FIELD_KEYWORDS.items():
            score = 0
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        score += 1
            field_scores[field] = score

        if not field_scores or max(field_scores.values()) == 0:
            return 'other'

        return max(field_scores, key=field_scores.get)
    
    def _extract_with_gpt(self, text: str) -> Dict:
        load_dotenv(find_dotenv(), override=True)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            # Fallback: rule-based extraction
            return self._extract_fallback(text)

        try:
            client = OpenAI(api_key=api_key)

            # Truncate to control cost
            text_truncated = text[:4000]
            detected_field = self.detect_field(text_truncated)

            prompt = f"""Extract structured information from this resume.
The candidate is in the "{detected_field}" field.

Resume text:
\"\"\"{text_truncated}\"\"\"

Resume text:
\"\"\"{text_truncated}\"\"\"

Return ONLY raw JSON, no markdown, no code fences:
{{
  "name": "candidate full name or null",
  "email": "email address or null",
  "phone": "phone number or null",
  "field": "primary field (technology, business, engineering, design, sciences, liberal_arts, healthcare, education, other)",
  "skills": ["skill1", "skill2", "skill3", ...],
  "projects": [
    {{"name": "project name", "description": "1-2 sentence description", "tech": ["relevant tools/methods used"]}}
  ],
  "experience": [
    {{"company": "company name", "role": "job title", "duration": "e.g., Summer 2023", "description": "1-2 sentence description"}}
  ],
  "education": [
    {{"institution": "university name", "degree": "degree name", "year": "graduation year"}}
  ]
}}

Extract at least 5 skills (relevant to the field), at least 1 project, and all experience/education entries.
For non-tech fields, "projects" can include research, campaigns, case studies, designs, etc.
For "tech" in projects, use relevant tools/methods (e.g., for marketing: "Google Analytics, SEO"; for finance: "Excel, Bloomberg"; for design: "Figma, Adobe Suite").
Be concise. Return only the JSON object."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            return json.loads(content)

        except Exception as e:
            print(f"⚠️  GPT extraction failed, using fallback: {e}")
            return self._extract_fallback(text)

    def _extract_fallback(self, text: str) -> Dict:
        """Rule-based extraction when GPT is unavailable. Field-agnostic."""
        # Extract email
        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
        email = email_match.group(0) if email_match else None

        # Extract phone
        phone_match = re.search(r'[\+\(]?[0-9][0-9\s\-\(\)]{8,}[0-9]', text)
        phone = phone_match.group(0).strip() if phone_match else None

        # Extract skills via multi-field keyword matching
        text_lower = text.lower()
        skills = set()
        for field, categories in self.FIELD_KEYWORDS.items():
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        skills.add(keyword)

        # Extract name (first non-empty line)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        name = lines[0] if lines else None
        if name and len(name.split()) > 4:
            name = ' '.join(name.split()[:3])

        return {
            'name': name,
            'email': email,
            'phone': phone,
            'skills': sorted(list(skills)),
            'projects': [],
            'experience': [],
        }

    def _mask_personal(self, data: Dict) -> Dict:
        """Mask personal metadata (name, email, phone) for privacy."""
        if not data:
            return data
        masked = data.copy()

        if masked.get('name'):
            masked['name'] = ' '.join(
                name[0] + '*' * (len(name) - 1) if len(name) > 1 else name
                for name in masked['name'].split()
            )

        # Mask email: "john@email.com" → "j***@email.com"
        if masked.get('email') and '@' in masked['email']:
            local, domain = masked['email'].split('@', 1)
            masked['email'] = local[0] + '*' * (len(local) - 1) + '@' + domain

        # Mask phone: "555-123-4567" → "***-***-4567"
        if masked.get('phone'):
            phone = masked['phone']
            digits = re.sub(r'\D', '', phone)
            if len(digits) >= 4:
                masked['phone'] = '*' * (len(phone) - 4) + phone[-4:]

        return masked


