# -*- coding: utf-8 -*-

from pyown.own import OWN, SCHEMA

class Statistics(OWN):

    def get_base_core(self, prefix="statistics"):
        # Base and Core
        self.logger.debug(f"{prefix}:getting statistics for types CoreConcept and BaseConcept")
        
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a owns:CoreConcept ; owns:containsWordSense ?s . }"
        own_core = self.graph.query(query).bindings[0]["count"].toPython()
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a owns:BaseConcept ; owns:containsWordSense ?s . }"
        own_base = self.graph.query(query).bindings[0]["count"].toPython()

        return own_base, own_core


    def get_defined(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Instantiated Synsets")

        # non void senses
        statistics = dict()
        for ss_type in ["NounSynset", "VerbSynset", "AdverbSynset", "AdjectiveSynset", "AdjectiveSatelliteSynset"]:
            # non void senses
            query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a owns:"+ss_type+"; owns:containsWordSense ?s . }"
            statistics[ss_type] = self.graph.query(query).bindings[0]["count"].toPython()

        # global
        ss_type = "Synset (total)"
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss owns:containsWordSense ?s . }"
        statistics[ss_type] = self.graph.query(query).bindings[0]["count"].toPython()

        return statistics


    def get_polysemy(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Polysemy")
        
        # non void senses
        statistics = dict()
        for ss_type in ["NounSynset", "VerbSynset", "AdverbSynset", "AdjectiveSynset", "AdjectiveSatelliteSynset"]:
            # polysemy
            query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a owns:"+ss_type+" ; owns:containsWordSense ?s1 ; owns:containsWordSense ?s2 . FILTER( ?s1 != ?s2 ) }"
            count_gt_1 = self.graph.query(query).bindings[0]["count"].toPython()
            query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a owns:"+ss_type+" ; owns:containsWordSense ?s1 . FILTER NOT EXISTS { ?ss owns:containsWordSense ?s2 . FILTER( ?s1 != ?s2 )}}"
            count_eq_1 = self.graph.query(query).bindings[0]["count"].toPython()

            statistics[ss_type] = count_eq_1, count_gt_1

        # global
        ss_type = "Synset (total)"
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss owns:containsWordSense ?s1 ; owns:containsWordSense ?s2 . FILTER( ?s1 != ?s2 ) }"
        count_gt_1 = self.graph.query(query).bindings[0]["count"].toPython()
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss owns:containsWordSense ?s1 . FILTER NOT EXISTS { ?ss owns:containsWordSense ?s2 . FILTER( ?s1 != ?s2 )}}"
        count_eq_1 = self.graph.query(query).bindings[0]["count"].toPython()

        statistics[ss_type] = count_eq_1, count_gt_1

        # results
        return statistics


    def get_multi_word_expressions(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Multi Word Expressions")

        # non void senses
        statistics = dict()
        name_pos_map = {"Noun":"n", "Verb":"v", "Adverb":"r", "Adjective":"a"}
        for name, pos in name_pos_map.items():
            # multi word expressions
            query = "SELECT (COUNT (DISTINCT ?w) as ?count) WHERE { ?w owns:pos \""+pos+"\"; owns:lemma ?l . FILTER REGEX( STR( ?l ), ' ') }"
            statistics[name] = self.graph.query(query).bindings[0]["count"].toPython()

        # global
        name = "Words (total)"
        query = "SELECT (COUNT ( DISTINCT ?w ) as ?count) WHERE { ?w owns:lemma ?l . FILTER REGEX( STR( ?l ), ' ') }"
        statistics[name] = self.graph.query(query).bindings[0]["count"].toPython()
        
        return statistics


    def get_relations(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Relations")

        statistics = dict()
        
        for pointer in self.pointers:
            senses_count = 0
            synsets_count = 0
            for subject, object in self.graph.subject_objects(pointer):
                if "wordsense" in subject and "wordsense" in object:
                    senses_count += 1
                elif "synset" in subject and "synset" in object:
                    synsets_count += 1
                else:
                    self.logger.warning(
                        f"couldn't classify subject {subject.n3()} "
                        f"or object {object.n3()} under relation {pointer.n3()}")
            # formats
            name = pointer
            name = name.replace(SCHEMA, "owns:")
            statistics[name] = senses_count, synsets_count
            
        return statistics
    

    def get_summary(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Summary")

        # synsets words and senses
        query = "SELECT (COUNT( DISTINCT ?s ) AS ?count) WHERE { ?s a owns:WordSense . }"
        senses = self.graph.query(query).bindings[0]["count"]
        query = "SELECT (COUNT( DISTINCT ?w ) AS ?count) WHERE { ?w a owns:Word . }"
        words = self.graph.query(query).bindings[0]["count"]
        
        return senses, words
