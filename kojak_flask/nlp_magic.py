from collections import defaultdict

import urllib
from bs4 import BeautifulSoup

import wikipedia
from wikipedia import DisambiguationError, PageError, RedirectError

import spacy
import textacy
from gensim.summarization import summarize, keywords

nlp = spacy.load('en')

#debugging
#import logging
#LOG_FILENAME = 'nlp_magic.log'
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)


### HTML-related functions
def create_hyperlink(url, display_text, attrs=""):
    '''Optional attrs is a string of tag attributes.
       
       create_hyperlink('www.google.com', 'Google', 
       ... attrs = 'class=link_class title="Custom Title"')'''
    
    hyperlink_format = '<a href="{link}" {attrs}>{text}</a>'
    return hyperlink_format.format(link=url, attrs=attrs, text=display_text)

def linkify_entity(ent_dict):
    '''Operates on extracted named entities. Returns HTML string.'''
    ent_type = ent_dict['label']
    text = ent_dict['text'] 
    url = get_wiki_page(text)['url']
    attrs = 'class="{ent_type}" title="{text}"'.format(ent_type=ent_type, text=text)
    return create_hyperlink(url, text, attrs=attrs)

def get_wiki_page(search_string, summary=False, content=False):
    '''Returns results from searching for search_string with wikipedia wrapper library. 
       Note: Makes a web request'''
    try:
        page = wikipedia.page(search_string)
        page_data = {"url":page.url,
                     "title":page.title}
        if content:
            page_data["content"] = page.content # Full text content of page.
        if summary:
            page_data["summary"] = page.summary # Summary section only.
    
    except DisambiguationError as e:
        return get_wiki_page(e.options[0]) #naively choose first option
    except Exception as e:
        return None
    
    return page_data





### spaCy and Textacy functions
def to_spacy_doc(raw_doc):
    '''Converts a raw string into a spaCy document'''
    return nlp(raw_doc)

def to_textacy_doc(raw_doc):
    '''Converts a raw string into a spaCy document, then a textacy document'''
    return textacy.Doc(nlp(raw_doc))

def extract_named_entities(text):
    '''Given a text document, extracts named entities using spaCy and builds a dict of metadata for each.
    
    Example Entity Type Labels:
    ORGANIZATION	Georgia-Pacific Corp., WHO
    PERSON	Eddy Bonte, President Obama
    LOCATION	Murray River, Mount Everest
    DATE	June, 2008-06-29
    TIME	two fifty a m, 1:30 p.m.
    MONEY	175 million Canadian Dollars, GBP 10.40
    PERCENT	twenty pct, 18.75 %
    FACILITY	Washington Monument, Stonehenge
    GPE	South East Asia, Midlothian
    '''
    
    doc = nlp(text)
    named_entities = defaultdict(dict)
    for ent in doc.ents:
        ent_name = ent.text
        named_entities[ent_name]['label'] = ent.label_
        named_entities[ent_name]['text'] = ent.text
        wiki_url = None #get_wiki_page(str(ent))['url']
        if wiki_url:
            named_entities[ent_name]['url'] = wiki_url
        
    return named_entities

def get_named_entity_data(ent_name):
    '''Returns the metadata dictionary for a given entity'''
    return named_entities_dict[ent_name]

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

def extract_summary(text, ratio=0.25):
    '''Wraps gensim summarize()'''
    return summarize(text, ratio)

def extract_keywords(text):
    '''Wraps gensim keywords(), returns a list of keyword strings'''
    return keywords(text).split()


def nlp_magic(text):
    '''NLP Magic: runs a standard pipeline and generates dictionary of outputs'''
    nlp_results_dict = {}    
    
    
    return nlp_results

    
if __name__ == "__main__":
    # execute only if run as a script
    nlp_magic()