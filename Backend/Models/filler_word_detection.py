import re
from collections import Counter

class FillerDetector:
    """
    Detects filler words and speech hesitations in transcribed text
    Week 3: Basic filler detection
    """
    
    def __init__(self, strictness="medium"):
        self.strictness = strictness
        
        # Core hesitations (always count these)
        core_fillers = {
            'um', 'uh', 'umm', 'uhh', 'ummm', 'uhhh',
            'er', 'err', 'erm',
            'ah', 'ahh', 'ahhh'
        }
        
        # Common discourse markers (medium strictness)
        common_fillers = {
            'like', 'you know', 'i mean', 
            'basically', 'actually', 'literally',
        }
        
        # Additional fillers (strict only)
        additional_fillers = {
            'sort of', 'kind of', 'you see',
            'obviously', 'honestly', 'frankly',
            'seriously', 'just', 'really', 'very',
            'well', 'so', 'anyway', 'right',
            'okay', 'alright'
        }
        
        # Build filler set based on strictness
        if strictness == "lenient":
            self.filler_words = core_fillers
        elif strictness == "medium":
            self.filler_words = core_fillers | common_fillers
        else:  # strict
            self.filler_words = core_fillers | common_fillers | additional_fillers
        
        # Phrases (multi-word fillers) - always include these
        self.filler_phrases = [
            'you know',
            'i mean',
            'sort of',
            'kind of',
        ]
    
    def detect_fillers(self, text):
        """
        Detect all filler words in text
        
        Args:
            text: Transcribed text string
        
        Returns:
            dict: Detailed filler detection results
        """
        if not text or not isinstance(text, str):
            return self._empty_result()
        
        text_lower = text.lower()
        words = text_lower.split()
        total_words = len(words)
        
        # Detect single-word fillers
        single_fillers = self._detect_single_fillers(words)
        
        # Detect multi-word phrases
        phrase_fillers = self._detect_phrase_fillers(text_lower)
        
        # Combine results
        all_fillers = single_fillers + phrase_fillers
        total_fillers = len(all_fillers)
        
        # Calculate statistics
        filler_frequency = Counter([f['word'] for f in all_fillers])
        filler_density = (total_fillers / total_words * 100) if total_words > 0 else 0
        
        # Categorize fillers
        categories = self._categorize_fillers(all_fillers)
        
        result = {
            'total_fillers': total_fillers,
            'total_words': total_words,
            'filler_density_percentage': round(filler_density, 2),
            'fillers_list': all_fillers,
            'filler_frequency': dict(filler_frequency.most_common()),
            'categories': categories,
            'score': self._calculate_filler_score(filler_density)
        }
        
        return result
    
    def _detect_single_fillers(self, words):
        """Detect single-word fillers"""
        fillers = []
        
        for i, word in enumerate(words):
            # Remove punctuation
            clean_word = re.sub(r'[^\w\s]', '', word).lower()
            
            if clean_word in self.filler_words:
                fillers.append({
                    'word': clean_word,
                    'position': i,
                    'type': 'single'
                })
        
        return fillers
    
    def _detect_phrase_fillers(self, text):
        """Detect multi-word filler phrases"""
        fillers = []
        
        for phrase in self.filler_phrases:
            # Find all occurrences of the phrase
            pattern = r'\b' + re.escape(phrase) + r'\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                fillers.append({
                    'word': phrase,
                    'position': match.start(),
                    'type': 'phrase'
                })
        
        return fillers
    
    def _categorize_fillers(self, fillers):
        """Categorize fillers by type"""
        categories = {
            'hesitations': [],
            'discourse_markers': [],
            'intensifiers': [],
            'apologetic': []
        }
        
        hesitations = {'um', 'uh', 'er', 'ah', 'umm', 'uhh', 'err', 'erm'}
        discourse = {'like', 'you know', 'i mean', 'basically', 'actually', 'literally', 'sort of', 'kind of'}
        intensifiers = {'really', 'very', 'just', 'so'}
        apologetic = {'sorry', 'excuse me'}
        
        for filler in fillers:
            word = filler['word']
            if word in hesitations:
                categories['hesitations'].append(word)
            elif word in discourse:
                categories['discourse_markers'].append(word)
            elif word in intensifiers:
                categories['intensifiers'].append(word)
            elif word in apologetic:
                categories['apologetic'].append(word)
        
        return {k: len(v) for k, v in categories.items()}
    
    def _calculate_filler_score(self, filler_density):

        if filler_density <= 2:
            return 100 
        elif filler_density <= 5:
            return 90   
        elif filler_density <= 8:
            return 80  
        elif filler_density <= 12:
            return 70   
        elif filler_density <= 15:
            return 60   
        elif filler_density <= 20:
            return 50   
        elif filler_density <= 25:
            return 40   # Poor - considerable work needed
        elif filler_density <= 30:
            return 30   # Very poor - extensive practice required
        else:
            # Even at 35%+, still give some points (20-25)
            return max(20, 30 - (filler_density - 30) * 0.5)
    
    def _empty_result(self):
        """Return empty result for invalid input"""
        return {
            'total_fillers': 0,
            'total_words': 0,
            'filler_density_percentage': 0,
            'fillers_list': [],
            'filler_frequency': {},
            'categories': {},
            'score': 100
        }
    
    def highlight_fillers(self, text):
        """
        Return text with fillers highlighted
        Useful for display in UI
        
        Args:
            text: Original text
        
        Returns:
            str: Text with fillers marked with **brackets**
        """
        if not text:
            return ""
        
        result = self.detect_fillers(text)
        highlighted = text
        
        # Sort fillers by position (reverse to maintain positions)
        fillers_sorted = sorted(result['fillers_list'], 
                              key=lambda x: x.get('position', 0), 
                              reverse=True)
        
        words = text.split()
        
        for filler in fillers_sorted:
            if filler['type'] == 'single':
                pos = filler['position']
                if 0 <= pos < len(words):
                    words[pos] = f"**{words[pos]}**"
        
        highlighted = ' '.join(words)
        
        # Highlight phrases
        for phrase in self.filler_phrases:
            pattern = r'\b' + re.escape(phrase) + r'\b'
            highlighted = re.sub(pattern, f"**{phrase}**", highlighted, flags=re.IGNORECASE)
        
        return highlighted


# ========== TESTING SCRIPT ==========

def test_filler_detector():
    """Test filler detection with sample text"""
    
    print("="*70)
    print("🔍 FILLER WORD DETECTION TEST")
    print("="*70)
    
    # Sample transcript with fillers
    test_text = """
    Um, so, like, I think artificial intelligence is, uh, really interesting. 
    You know, I've been working on, um, several projects. Basically, what I mean is, 
    uh, AI can solve, like, real-world problems. Sorry, I mean, it's actually very 
    powerful. So, yeah, that's kind of what I wanted to say.
    """
    
    print("\n📝 Test Text:")
    print(test_text.strip())
    
    # Test with different strictness levels
    for strictness in ["lenient", "medium", "strict"]:
        print(f"\n{'='*70}")
        print(f"Testing with '{strictness.upper()}' strictness:")
        print('='*70)
        
        detector = FillerDetector(strictness=strictness)
        result = detector.detect_fillers(test_text)
        
        print(f"\n🔢 Results:")
        print(f"  • Total Words: {result['total_words']}")
        print(f"  • Total Fillers: {result['total_fillers']}")
        print(f"  • Filler Density: {result['filler_density_percentage']}%")
        print(f"  • Filler Score: {result['score']}/100")
        
        if result['filler_frequency']:
            print(f"\n📋 Detected Fillers:")
            for filler, count in list(result['filler_frequency'].items())[:10]:
                print(f"  • '{filler}': {count} times")
    
    print("\n" + "="*70)
    print("💡 RECOMMENDATION: Use 'medium' strictness for interviews")
    print("="*70)
    print("\nExplanation:")
    print("  • Lenient: Only counts obvious hesitations (um, uh)")
    print("  • Medium: Counts common fillers (recommended)")
    print("  • Strict: Counts everything (may be too harsh)")
    print("\n✅ FILLER DETECTION TEST COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    test_filler_detector()