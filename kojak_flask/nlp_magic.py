from collections import defaultdict

import urllib
import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree

import wikipedia
from wikipedia import DisambiguationError, PageError, RedirectError

import spacy
import textacy
#from gensim.summarization import summarize  # Warning: slow to load

nlp = spacy.load('en')

import proselint
from proselint.tools import errors_to_json
import json

import re

editor_history = []

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


def dbpedia_prefix_search(query_string, api_host='http://localhost:1111', query_class=''):
    '''Returns list of dicts from dbpedia API search. Keys are: label, uri, description'''
    api_string = api_host+"/api/search/PrefixSearch?"
    query_class = 'QueryClass=' + query_class + "&"
    query_string = 'QueryString=' + query_string
    request_string = api_string + query_class + query_string
    
    response = requests.get(request_string)
    xmltree = ElementTree.fromstring(response.content)
    
    lookup = './/{http://lookup.dbpedia.org/}'
    results = xmltree.findall(lookup+"Result")
    if not results:
        return None
    
    results_list = []
    for i, result in enumerate(results):
        results_list.append({
            'label': xmltree.findall(lookup+"Label")[i].text,
            'uri'  : xmltree.findall(lookup+"URI")[i].text,
            'description' : xmltree.findall(lookup+"Description")[i].text
        })
    return results_list

def get_dbpedia_results(queries):
    '''Given a list of query strings, returns a list of result dicts.'''
    results = []
    for query in queries:
        result_for_query = dbpedia_prefix_search(query)
        if result_for_query:
            results.append(result_for_query[0])
    return results

def get_dbpedia_result_text(queries):
    '''Given a list of query strings, returns a list of (label+description) strings '''
    results = get_dbpedia_results(queries)
    
    results_strings = [str(r['label'] +": "+ r['description']) 
                       for r in results if r['description']]
    return list(set(results_strings))


### Proselint
def linter_suggestions(text):
    ''' Returns suggestions as a list of dicts. Each dict is a suggestion with the following properties:
    (check, message, line, column, start, end, extent, severity, replacements)
    '''
    suggestions = proselint.tools.lint(text)
    json_string = errors_to_json(suggestions) 
    json_dict = json.loads(json_string)
    return json_dict['data']['errors']


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
    ts = textacy.text_stats.TextStats(doc)
    return ts.readability_stats

def get_semantic_key_terms(doc, top_n_terms=10, filtered=True):
    '''Gets key terms from semantic network. '''
    if not isinstance(doc, textacy.doc.Doc):
        doc = to_textacy_doc(doc)
    term_prob_pairs = textacy.keyterms.key_terms_from_semantic_network(doc,window_width=3,ranking_algo=u'pagerank')
    max_keyterm_weight = term_prob_pairs[0][1]
    
    # keep keyterms if they're at least half as important as the most important keyterm
    # term[0] is the word, term[1] is its keyterm-ness.
    if filtered:
        terms = [[term[0], term[1]] for term in term_prob_pairs if term[1] >= 0.5*(max_keyterm_weight)]
    else:
        terms = term_prob_pairs
    
    #textacy.keyterms.aggregate_term_variants(terms) #aggregates terms that are variations of each other
    
    return terms[:top_n_terms]

def extract_summary(text, ratio=0.1):
    '''Wraps gensim summarize()'''
    return summarize(text, ratio)

def extract_keywords(text):
    '''Wraps textacy keywords function, returns a list of keyword strings'''
    if len(text.split(" ")) < 3:
        return " "
    return textacy.keyterms.key_terms_from_semantic_network(to_textacy_doc(text))

def get_sentences(doc):
    '''Returns a list of spacy spans.'''
    if not isinstance(doc, textacy.doc.Doc):
        doc = to_textacy_doc(doc)
    return list(doc.sents)

#def get_completions(doc):
#    '''Accepts string or textacy doc. Returns list of strings.'''
#    #if not isinstance(doc, textacy.doc.Doc):
#    #    doc = to_textacy_doc(doc)
#    completions = []
#    
#    sentences = [str(sent) for sent in get_sentences(doc)]
#    last_sent = sentences[-1]
#    
#    capture_pattern = "(?:##)[ \w]+(?:##)"
#    match = re.search(capture_pattern, doc)
#    if match: ## is the flag to suggest
#        query = match.group(0).replace("##", "").strip()
#        
#        lookup = get_dbpedia_result_text([query])
#        
#        completions = lookup
#    return completions

def get_completions(doc):
    '''Accepts string or textacy doc. Returns list of strings.'''
    if not isinstance(doc, textacy.doc.Doc):
        doc = to_textacy_doc(doc)
    
    ents = [str(ent) for ent in textacy.extract.named_entities(doc)]   
    completions = get_dbpedia_result_text(ents)    
        
        
        
    return completions




def nlp_magic(text):
    '''NLP Magic: runs a standard pipeline and generates dictionary of outputs'''
    nlp_results_dict = {}    
    
    
    return nlp_results

    
if __name__ == "__main__":
    # execute only if run as a script
    nlp_magic()