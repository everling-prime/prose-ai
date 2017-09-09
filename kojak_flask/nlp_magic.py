import urllib
from bs4 import BeautifulSoup

import wikipedia

import spacy
import textacy

nlp = spacy.load('en')


### HTML-related functions
def create_hyperlink(url, display_text, attrs=""):
    '''Optional attrs is a string of tag attributes.
       
       create_hyperlink('www.google.com', 'Google', 
       ... attrs = 'class=link_class title="Custom Title"')'''
    
    hyperlink_format = '<a href="{link}" {attrs}>{text}</a>'
    return hyperlink_format.format(link=url, attrs=attrs, text=display_text)

def linkify_entity(named_entity_tuple):
    '''Operates on tuples from get_named_entities(). Returns HTML string.'''
    ent_type, label, url = named_entity_tuple #unpacks tuple
    attrs = 'class="{ent_type}" title="{ent_type}"'.format(ent_type=ent_type)
    return create_hyperlink(url, label, attrs=attrs)

def get_wiki_page(search_string):
    '''Returns URL found by searching for search_string with wikipedia wrapper library. 
       Note: Makes a web request'''
    page = wikipedia.page(search_string)
    content = page.content # Content of page.
    summary = page.summary(sentences=2)
    return page.url, content, summary

def strip_HTML_tags(html, url=None):
    '''Removes HTML tags from raw HTML input string. 
       Optional url parameter to scrape a given website with urllib.
       Parses text with BeautifulSoup, splits into tokens, rejoins stripped tokens'''
    if url:
        html = urllib.urlopen(url).read()
    soup = BeautifulSoup(html)

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text





### spaCy and Textacy functions
def to_spacy_doc(raw_doc):
    '''Converts a raw string into a spaCy document'''
    return nlp(raw_doc)

def to_textacy_doc(raw_doc):
    '''Converts a raw string into a spaCy document, then a textacy document'''
    return textacy.Doc(nlp(raw_doc))

def get_named_entities(text):
    doc = nlp(text)
    named_entities_tuples = []
    for ent in doc.ents:
        wiki_url = get_wiki_page(str(ent))[0]
        if wiki_url:
            named_entities_tuples.append((ent.label_, ent.text, wiki_url))
        else:
            named_entities_tuples.append((ent.label_, ent.text))
    
    return named_entities_tuples

def get_readability_stats(doc):
    '''Gets readability stats for a textacy doc. 
       Converts doc to textacy doc first if necessary'''
    if not isinstance(doc, textacy.doc.Doc):
        doc = to_textacy_doc(doc)      
    ts = text_stats.TextStats(doc)
    return ts.readability_stats

def get_semantic_key_terms(doc):
    '''Uses textacy to get key terms from semantic network for input doc'''
    if not isinstance(doc, textacy.doc.Doc):
        doc = to_textacy_doc(doc)
    term_prob_pairs = textacy.keyterms.key_terms_from_semantic_network(doc)
    terms = [term[0] for term in term_prob_pairs]
    return terms






def nlp_magic(text):
    '''NLP Magic: runs a standard pipeline and generates dictionary of outputs'''
    nlp_results = []
    
    nlp_results.append(get_named_entities(text))
    
    
    
    return nlp_results

    
if __name__ == "__main__":
    # execute only if run as a script
    nlp_magic()