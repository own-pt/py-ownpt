# -*- coding: utf-8 -*-

from tqdm import tqdm
from rdflib import Graph, URIRef
from pyown.own import OWN, SCHEMA

class Compare(OWN):
    
    def __init__(self, graph:Graph, dump:dict):
        super().__init__(graph)
        self.dump = [doc["_source"] for doc in dump]
        self.docs = {synset["doc_id"]:synset for synset in self.dump}


    def compare_items(self):
        """"""

        # compares items
        _, report_word = self.compare_item_own_dump(item_name="word_pt")
        _, report_gloss = self.compare_item_own_dump(item_name="gloss_pt")
        _, report_example = self.compare_item_own_dump(item_name="example_pt")
        report_word = report_word["docs"]
        report_gloss = report_gloss["docs"]
        report_example = report_example["docs"]

        # joins results
        report = dict()
        for doc_id in report_word:
            report[doc_id] = dict()

            report[doc_id]["compare"] = all({
                report_word[doc_id]["word_pt"]["compare"],
                report_gloss[doc_id]["gloss_pt"]["compare"],
                report_example[doc_id]["example_pt"]["compare"]
            })
            
            report[doc_id].update(report_word[doc_id])
            report[doc_id].update(report_gloss[doc_id])
            report[doc_id].update(report_example[doc_id])
        
        return report


    def compare_item_own_dump(self, item_name):
        """"""

        # reports
        compare = True
        report = {
            "docs":dict(), 
            "count":{"dump":0, "rdf":0, "both":0}}
        
        # query
        query = self._get_query(item_name)

        # start comparing
        self.logger.info(f"start comparing item {item_name}:")
        for synset in tqdm(self.dump):
            doc_id = synset['doc_id']

            result, items, itemsd, itemso = self._compare_item(synset, item_name, query)
            
            # update report
            report["count"]["both"] += len(items)
            report["count"]["dump"] += len(itemsd)
            report["count"]["rdf"] += len(itemso)
            
            report["docs"][doc_id] = dict()
            report["docs"][doc_id][item_name] = {"compare":result, "both":items, "dump":itemsd, "rdf":itemso}

            # displays debug info
            if not result:
                compare = False
                self.logger.debug(f"synset {doc_id}:words: comparing resulted False:"
                                f"\n\t {item_name} {itemsd} found only in dump"
                                f"\n\t {item_name} {itemso} found only in rdf"
                                f"\n\t {item_name} {items} found in both documents")
        
        self.logger.info(f"{item_name}: comparing resulted '{compare}':"
                        f"\n\t {item_name}:{report['count']['dump']} found only in dump"
                        f"\n\t {item_name}:{report['count']['rdf']} found only in rdf"
                        f"\n\t {item_name}:{report['count']['both']} found in both documents")

        # returns report
        return compare, report


    def compare_antonymof_own_dump(self):
        """"""

        map_pointers = {"wn30_pt_antonymOf":SCHEMA.antonymOf}
        return self._compare_pointers_own_dump(map_pointers)

    
    def compare_morpho_own_dump(self):
        """"""

        # morphosemantic links
        pointers_uri_map = {  
            "wn30_pt_property": SCHEMA.property,
            "wn30_pt_result": SCHEMA.result,
            "wn30_pt_state": SCHEMA.state,
            "wn30_pt_undergoer": SCHEMA.undergoer,
            "wn30_pt_uses": SCHEMA.uses,
            "wn30_pt_vehicle": SCHEMA.vehicle,
            "wn30_pt_event": SCHEMA.event,
            "wn30_pt_instrument": SCHEMA.instrument,
            "wn30_pt_location": SCHEMA.location,
            "wn30_pt_material": SCHEMA.material,
            "wn30_pt_agent": SCHEMA.agent,
            "wn30_pt_bodyPart": SCHEMA.bodyPart,
            "wn30_pt_byMeansOf": SCHEMA.byMeansOf
        }

        return self._compare_pointers_own_dump(pointers_uri_map)


    def _compare_pointers_own_dump(self, map_pointers:dict):
        """"""

        compare = True
        reports = dict()

        for pointer_name, pointer_uri in map_pointers.items():
            compare_i, reports[pointer_name] = self._compare_pointer_own_dump(pointer_name, pointer_uri)
            compare = compare if compare_i else False
        
        return compare, reports


    def _compare_pointer_own_dump(self, pointer_name, pointer_uri):
        """"""

        # reports
        compare = True
        report = {
            "count":{"dump":0, "rdf":0, "both":0},
            "pairs":{"dump":[], "rdf":[], "both":[]}}

        self.logger.info(f"start comparing pointer '{pointer_name}':")
        for synset in tqdm(self.dump):
            doc_id = synset['doc_id']

            result, pairs, pairsd, pairso = self._compare_pointers(synset, pointer_name, pointer_uri)

            # update report
            report["count"]["both"] += len(pairs)
            report["count"]["dump"] += len(pairsd)
            report["count"]["rdf"] += len(pairso)
            report["pairs"]["both"] += pairs
            report["pairs"]["dump"] += pairsd
            report["pairs"]["rdf"] += pairso
            
            # display debug
            if not result:
                compare = False
                self.logger.debug(f"synset {doc_id}:{pointer_name}: comparing resulted False:"
                                f"\n\t pairs {pairsd} found only in dump"
                                f"\n\t pairs {pairso} found only in rdf"
                                f"\n\t pairs {pairs} found in both documents")
        
        self.logger.info(f"{pointer_name}: comparing resulted '{compare}':"
                        f"\n\t {report['count']['dump']} pairs found only in dump"
                        f"\n\t {report['count']['rdf']} pairs found only in rdf"
                        f"\n\t {report['count']['both']} pairs found in both documents")

        # returns report
        return compare, report


    def _compare_item(self, synset:dict, item_name:str, query:str):
        """"""  
        compare = True
        
        # report words
        items = []
        itemso = []
        itemsd = synset[item_name].copy() if item_name in synset else []
        itemsd = [item.strip() for item in itemsd]
        itemsd = list(set(itemsd))  # unique occurrences

        # finds all wordsenses, and its words
        doc_id = synset["doc_id"]
        synset = self._get_synset_by_id(doc_id)
        result = self.graph.query(query.format(synset = synset.n3()))
        
        # compares words in synset with dump
        for item, in result:
            item = item.toPython().strip()

            # checks if word exists in dump
            if item in itemsd:
                items.append(item)
                itemsd.remove(item)
            else:
                itemso.append(item)

        # check if unique words are void
        if len(itemsd) > 0: compare = False
        if len(itemso) > 0: compare = False
        
        return compare, items, itemsd, itemso


    def _compare_pointers(self, synset:dict, pointer_name:str, pointer_uri:URIRef):
        """"""
        compare = True
        
        # pointers
        pairs = []
        pairso = []
        pairsd = []

        # find pairs with source in this synset
        if pointer_name in synset:
            for pointer in synset[pointer_name]:
                # source senses/synset
                source = self._get_source_target(synset, pointer, "source_word")
                
                # target senses/synset
                target_synset = self.docs[pointer["target_synset"]]
                target = self._get_source_target(target_synset, pointer, "target_word")
                
                # pairs
                if source and target:
                    pairsd.append((source, target))

        # finds pointers
        doc_id = synset["doc_id"]
        query = ("SELECT ?ss ?sw ?swl ?ts ?tw ?twl WHERE{{"
                    "?s owns:synsetId \"{synset}\" ."
                    "?s owns:containsWordSense ?ss ."
                    "?ss {pointer} ?ts ."
                    "?ss owns:word ?sw . ?sw owns:lemma ?swl ."
                    "?ts owns:word ?tw . ?tw owns:lemma ?twl . }}")
        result = self.graph.query(query.format(
                    synset = doc_id,
                    pointer = pointer_uri.n3()))
        

        # compares words in synset with dump
        for _, _, source_word, _, _, target_word in result:
            source_word = source_word.toPython().strip()
            target_word = target_word.toPython().strip()
            pair = (source_word, target_word)

            # checks if pair exists in dump
            if pair in pairsd:
                pairs.append(pair)
                pairsd.remove(pair)
            else:
                pairso.append(pair)

        # check if unique words are void
        if len(pairsd) > 0: compare = False
        if len(pairso) > 0: compare = False
        
        return compare, pairs, pairsd, pairso


    def _get_source_target(self, synset, pointer, key):
        """"""
        
        word = pointer[key] if key in pointer else None
        words = synset["word_pt"] if "word_pt" in synset else []

        if word is None:
            return synset
        if word in words:
            return word
        
        return None


    def _get_query(self, item_name):
        """"""

        if item_name == "word_pt":
            return "SELECT ?wl WHERE {{ {synset} owns:containsWordSense/owns:word/owns:lemma ?wl . }}"
        if item_name == "gloss_pt":
            return "SELECT ?gl WHERE {{ {synset} owns:gloss ?gl . }}"
        if item_name == "example_pt":
            return "SELECT ?ex WHERE {{ {synset} owns:example ?ex . }}"
        
        raise Exception(f"not a valid option for comparing: {item_name}")

