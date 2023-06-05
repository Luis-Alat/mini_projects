import re
import string

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag

from wordcloud import STOPWORDS

from bs4 import BeautifulSoup

stop_words_word = set(STOPWORDS)
stop_words_nltk = set(stopwords.words("english"))
stop_words = stop_words_word.union(stop_words_nltk)
stop_words_pattern = re.compile(fr"\b(?:{'|'.join(stop_words)})\b")
def RemoveStopWords(sentence:str) -> str:
    return stop_words_pattern.sub(" ", sentence)

class CleanText:
    
    def __init__(self):
        
        self.r_link_compiled = self.__RemoveLinksPattern()
        self.r_punc_compiled = self.__RemovePunctuationsPattern()
        self.r_nonp_compiled = self.__RemoveNonPrintablePattern()
        self.r_emoj_compiled = self.__RemoveEmojisPattern()
        self.r_whit_compiled = self.__RemoveWhiteSpaces()
        self.r_hash_compiled = self.__RemoveHashTagsPattern()
        self.r_ment_compiled = self.__RemoveMentionsPattern()
        
        
    def __RemoveHtml(self, text):
        return BeautifulSoup(text, "lxml").text

    def __RemoveLinksPattern(self):
        return re.compile(r'https?://\S+')

    def __RemovePunctuationsPattern(self):
        punctuations = string.punctuation.replace("?","").replace("'","").replace("!","")
        punctuations = punctuations.replace(".","").replace("%","").replace("#","").replace("$","")
        return re.compile(r'[' + re.escape(punctuations) + ']+')
    
    def __RemoveNonPrintablePattern(self):
        return re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\r]')

    def __RemoveEmojisPattern(self):
        emoji_patterns = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002500-\U00002BEF"
            u"\U00002702-\U000027B0"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010ffff"
            u"\u2640-\u2642" 
            u"\u2600-\u2B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"
            u"\u3030"
                        "]+", re.UNICODE)
        
        return emoji_patterns
    
    def __RemoveWhiteSpaces(self):
        return re.compile(r"\s+")
    
    def __RemoveHashTagsPattern(self):
        return re.compile(r'#\w+')
    
    def __RemoveMentionsPattern(self):
        return re.compile(r'@\w+')

    def Cleaner(self, text:str, on:str = "youtube"):
        
        '''
        Parameters
        ----------
        
        text:str
            Text to clean
        
        on:str; ["twitter","youtube"]
            If on='twitter', add some extra steps to clean mentions @ and hashtags #
        
        '''
        
        clean_text = str(text).lower()
        clean_text = self.r_link_compiled.sub(" ", clean_text)
        clean_text = self.__RemoveHtml(clean_text)
        
        if on == "twitter":
            clean_text = self.r_hash_compiled.sub(" ", clean_text)
            clean_text = self.r_ment_compiled.sub(" ", clean_text)
        
        clean_text = self.r_emoj_compiled.sub(" ", clean_text)
        clean_text = self.r_nonp_compiled.sub(" ", clean_text)
        clean_text = self.r_punc_compiled.sub(" ", clean_text)
        clean_text = self.r_whit_compiled.sub(" ", clean_text)
        
        return clean_text

def TruncateText(text, max_length):
    return str(text)[:max_length]

def LemmatizeWithPos(text, as_list = True):
    
    lemmatizer = WordNetLemmatizer()
    
    pos_tag_dict = {
        "J": wordnet.ADJ,
        "N": wordnet.NOUN,
        "V": wordnet.VERB,
        "R": wordnet.ADV
    }
    
    tokens = word_tokenize(text)
    pos = pos_tag(tokens)
    new_sentence = []
        
    for token, tag_pos in pos:
        
        first_letter_pos = tag_pos[0].upper() 
        word_net_value = pos_tag_dict.get(first_letter_pos, "n")
        lemma = lemmatizer.lemmatize(word = token, pos = word_net_value)

        new_sentence.append(lemma)
        
    if as_list:
        return new_sentence
    else:
        return " ".join(new_sentence)


if __name__ == "__main__":
    sentence = "Hi, how are you!"
    print(sentence)
    cleaner = CleanText()
    sentence = cleaner.Cleaner(sentence, on="twitter")
    sentence = TruncateText(sentence, 700)
    sentence = LemmatizeWithPos(sentence)
    print(sentence)
