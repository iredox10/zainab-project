import nltk
import numpy as np
import string
from nltk.stem.lancaster import LancasterStemmer

# Initialize stemmer
stemmer = LancasterStemmer()

# Download required NLTK data to /tmp since the function is read-only
nltk.data.path.append("/tmp/nltk_data")
for resource in ['punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        nltk.download(resource, download_dir="/tmp/nltk_data")

def clean_up_sentence(sentence):
    # tokenize the pattern
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words if word not in string.punctuation]
    return sentence_words

def bag_of_words(sentence, words):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words
    bag = [0] * len(words)  
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s: 
                bag[i] = 1
    return np.array(bag)

def get_similarity(input_vec, pattern_vec):
    """Simple dot product similarity for matching"""
    return np.dot(input_vec, pattern_vec)

def predict_class(sentence, patterns_data, threshold=0.75):
    """
    sentence: User input string
    patterns_data: List of dicts {'text': '...', 'tag': '...'}
    """
    # Create vocabulary from all patterns
    vocabulary = []
    for p in patterns_data:
        vocabulary.extend(clean_up_sentence(p['text']))
    vocabulary = sorted(list(set(vocabulary)))

    # Get input vector
    input_vec = bag_of_words(sentence, vocabulary)
    
    results = []
    for p in patterns_data:
        p_vec = bag_of_words(p['text'], vocabulary)
        score = get_similarity(input_vec, p_vec)
        
        # Normalize score (count of matching words / total words in input)
        input_len = len(clean_up_sentence(sentence))
        if input_len > 0:
            normalized_score = score / input_len
        else:
            normalized_score = 0
            
        results.append((p['intent_tag'], normalized_score))

    # Sort by strength of matching
    results.sort(key=lambda x: x[1], reverse=True)
    
    if results and results[0][1] >= threshold:
        return results[0][0] # Return the tag
    return None # Fallback
