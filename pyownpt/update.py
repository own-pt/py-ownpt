# -*- coding: utf-8 -*-

from rdflib import Graph, Namespace, URIRef
from rdflib import Literal, XSD, RDF, RDFS, SKOS, OWL

# global
OWNPT = Namespace("https://w3id.org/own-pt/wn30/schema/")

WORD = Namespace("https://w3id.org/own-pt/wn30-pt/instances/word-")
SYNSET_PT = Namespace("https://w3id.org/own-pt/wn30-pt/instances/synset-")
WORDSENSE = Namespace("https://w3id.org/own-pt/wn30-pt/instances/wordsense-")


def update_ownpt_from_dump(ownpt:Graph, wn:dict):
    """"""

    # removing WordSense from Synset
    ownpt.remove((None, OWNPT.containsWordSense, None))
    # removing properties of WordSense
    ownpt.remove((None, RDF.type, OWNPT.WordSense))
    ownpt.remove((None, OWNPT.wordNumber, None))
    ownpt.remove((None, RDFS.label, None))
    # removing Word from WordSense
    ownpt.remove((None, OWNPT.word, None))
    # removing properties of Word
    ownpt.remove((None, RDF.type, OWNPT.Word))
    ownpt.remove((None, OWNPT.lexicalForm, None))

    # removing gloss from from Synset
    ownpt.remove((None, OWNPT.gloss, None))

    # removing example from from Synset
    ownpt.remove((None, OWNPT.example, None))
    
    # updates synsets
    for synset in wn:
        _update_synset(ownpt, synset)

    return ownpt


def _update_synset(ownpt:Graph, synset:dict):
    """"""

    doc_id = synset["doc_id"]
    synset_pt = SYNSET_PT[doc_id]
    
    # adding word-pt
    word_pt = synset["word_pt"] if "word_pt" in synset else []
    for i, word in enumerate(word_pt, start=1):
        word_pt = WORD[word.replace(" ", "_")]  
        word_sense = WORDSENSE[f"{doc_id}-{i}"]

        ownpt.add((synset_pt, OWNPT.containsWordSense, word_sense))
        
        # word sense
        ownpt.add((word_sense, RDF.type, OWNPT.WordSense))
        ownpt.add((word_sense, OWNPT.wordNumber, Literal(i)))
        ownpt.add((word_sense, RDFS.label, Literal(word, lang="pt")))

        # word form
        ownpt.add((word_sense, OWNPT.word, word_pt))
        ownpt.add((word_pt, RDF.type, OWNPT.Word))
        ownpt.add((word_pt, OWNPT.lexicalForm, Literal(word, lang="pt")))


    # adding gloss-pt
    gloss_pt = synset["gloss_pt"] if "gloss_pt" in synset else []
    for i, gloss in enumerate(gloss_pt, start=1):
        ownpt.add((synset_pt, OWNPT.gloss, Literal(gloss, lang="pt")))

    # adding example-pt
    example_pt = synset["example_pt"] if "example_pt" in synset else []
    for i, example in enumerate(example_pt, start=1):
        ownpt.add((synset_pt, OWNPT.example, Literal(example, lang="pt")))


def dump_update(
    doc_wn = [],
    doc_suggestions = [],
    doc_votes = [],
    users_senior=[],
    trashold_senior=1,
    trashold_junior=2):
    """"""

    # acesses only sources
    wn = [item["_source"] for item in doc_wn]
    votes = [item["_source"] for item in doc_votes]
    suggestions = [item["_source"] for item in doc_suggestions]

    # filter suggestions
    suggestions = _filter_suggestions(suggestions, votes, users_senior, trashold_senior, trashold_junior)

    # joins synsets and suggestions
    f_idl = lambda x: x["doc_id"]
    f_idr = lambda x: x["doc_id"]
    zipped = _left_zip_by_id(wn, suggestions, f_idl, f_idr)

    # apply suggestions
    for synset, suggestions in zipped:
        _apply_suggestions(synset, suggestions)
    
    return doc_wn


def _apply_suggestions(synset:dict, suggestions:list):
    for suggestion in suggestions:
        _apply_suggestion(synset, suggestion)

def _apply_suggestion(synset:dict, suggestion):
    action = suggestion["action"]
    params = suggestion["params"]

    if action == "add-word-pt":
        _add_parameter(synset, "word_pt", params)
    elif action == "add-gloss-pt":
        _add_parameter(synset, "gloss_pt", params)
    elif action == "add-example-pt":
        _add_parameter(synset, "example_pt", params)
    elif action == "remove-word-pt":
        _remove_parameter(synset, "word_pt", params)
    elif action == "remove-gloss-pt":
        _remove_parameter(synset, "gloss_pt", params)
    elif action == "remove-example-pt":
        _remove_parameter(synset, "example_pt", params)
    else:
        print(f"Not a valid action: {action}")
        # raise Exception(f"Not a valid action: {action}")

    return synset


def _add_parameter(synset, key, params):
    """"""

    if key in synset:
        synset[key].append(params)
    else:
        synset[key] = [params]

def _remove_parameter(synset, key, params):
    """"""

    if key in synset:
        if params in synset[key]:
            synset[key].remove(params)
        else:
            print(f"Param not in synset {synset['doc_id']} key {key}: {params} not in {synset[key]}")
            # raise Exception(f"Param not in synset {synset['doc_id']} key {key}: {params}")
    else:
        print(f"Key not in synset: {key}")
        # raise Exception(f"Key not in synset: {key}")


def _filter_suggestions(
    suggestions:list,
    votes:list,
    users_senior:list,
    trashold_senior:int,
    trashold_junior:int):
    """"""

    # joins suggestions and votes
    f_idl = lambda x: x["id"]
    f_idr = lambda x: x["suggestion_id"]
    zipped = _left_zip_by_id(suggestions, votes, f_idl, f_idr)

    # apply filter rules and return
    return [x[0] for x in zipped if _rules(*x,users_senior,trashold_senior,trashold_junior)]


def _rules(suggestion, votes:list, users_senior:list, trashold_senior:int, trashold_junior:int):
    """"""

    r1 = suggestion["status"] == "new"
    r2 = suggestion["action"] != "comment"
    score = sum([vote["value"] for vote in votes])
    r3 = score >= trashold_senior and suggestion["user"] in users_senior or score >= trashold_junior

    return all([r1,r2,r3])


def _left_zip_by_id(listl, listr, f_idl, f_idr):
    """"""

    # review eficiency
    zipped = {f_idl(l):{"l":l,"r":[]} for l in listl}
    for itemr in listr:
        _id = f_idr(itemr)
        if _id in zipped:
            zipped[_id]["r"].append(itemr)
        else:
            print(f"Got invalid id to zip: {_id}")
            # raise Exception(f"Got invalid id to zip: {_id}")

    return [(item["l"],item["r"]) for item in zipped.values()]