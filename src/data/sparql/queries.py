def COMPARISONS_CONTRIBUTINOS_AND_THEIR_PAPERS(n_contributions, blacklist=None):

    if blacklist:
        blacklist = ','.join(['orkgr:{}'.format(x) for x in blacklist])

    return """PREFIX orkgp: <http://orkg.org/orkg/predicate/>
PREFIX orkgc: <http://orkg.org/orkg/class/>
PREFIX orkgr: <http://orkg.org/orkg/resource/>

SELECT DISTINCT ?comparison ?comparison_label
                ?contribution
                ?paper ?paper_title ?doi 
                ?research_field ?research_field_label
                ?research_problem ?research_problem_label
        WHERE {{
            ?comparison rdf:type orkgc:Comparison ;
                         orkgp:compareContribution ?contribution ;
                         rdfs:label ?comparison_label .
          
            ?paper orkgp:P31 ?contribution ;
                   rdfs:label ?paper_title ;
                   orkgp:P30 ?research_field .
          
            ?research_field rdfs:label ?research_field_label .

          
            OPTIONAL {{?contribution orkgp:P32 ?research_problem .
                     ?research_problem rdfs:label ?research_problem_label}}

            OPTIONAL {{ ?paper orkgp:P26 ?doi }}
          
          {{
            SELECT ?comparison (COUNT(*) AS ?n_contributions)
            WHERE {{
               ?comparison rdf:type orkgc:Comparison ;
                         orkgp:compareContribution ?contribution .
               ?contribution rdf:type orkgc:Contribution .
               ?paper orkgp:P31 ?contribution .
               
               FILTER (?comparison NOT IN ({}))
            }}
            GROUP BY ?comparison
            HAVING (COUNT(*) >= {})
          }}
          
        }}
ORDER BY ?comparison""".format(blacklist, n_contributions)


def PAPER_CONTRIBUTIONS(paper_id):
    return """PREFIX orkgp: <http://orkg.org/orkg/predicate/>
            PREFIX orkgc: <http://orkg.org/orkg/class/>
            PREFIX orkgr: <http://orkg.org/orkg/resource/>

            SELECT DISTINCT ?contribution
                    WHERE {{
                           orkgr:{} orkgp:P31 ?contribution .  
                    }}
            """.format(paper_id)
