import pandas as pd
import os
import json

attribute_source = "infores:biothings-multiomics-drugapprovals"
attribute_data_source = "infores:isb-wellness"
faers = "infores:faers"
dailymed = "infores:dailymed"
kgInfoUrl = "https://db.systemsbiology.net/gestalt/cgi-pub/KGinfo.pl?id="

def load_content(data_folder):
    edges_file_path = os.path.join(data_folder, "drug_approvals_kg_edges_v0.2.tsv")
    nodes_file_path = os.path.join(data_folder, "drug_approvals_kg_nodes_v0.2.tsv")

    nodes_data = pd.read_csv(nodes_file_path, sep='\t')
    id_name_mapping = {}
    id_type_mapping = {}
    for index,row in nodes_data.iterrows():
        id_name_mapping[row["id"]] = row["name"]
        id_type_mapping[row["id"]] = row["category"]

    edges_data = pd.read_csv(edges_file_path, sep='\t')
    for index,line in edges_data.iterrows():
        subj = line['subject']
        pred = line['predicate']
        obj  = line['object']
        if subj and pred and subj.split(':')[0] and obj.split(':')[0]:

            prefix = obj.split(':')[0].replace(".","_")
            disease = {
                prefix.lower(): obj,
                "name": id_name_mapping[obj],
            }

            # properties for predicate/association
            edge_attributes = []

            # approval status
            status = ""
            
            # sources
            edge_sources = []
            if pred == 'treats':
                status = "approved_for_condition"
                edge_sources = [
                    {
                        "resource_id": attribute_source,
                        "resource_role": "primary_knowledge_source",
                        "source_record_urls": [ kgInfoUrl + line['id'] ]
                    },
                    {
                        "resource_id": dailymed,
                        "resource_role": "supporting_data_source"
                    },
                    {
                        "resource_id": faers,
                        "resource_role": "supporting_data_source"
                    }
                ]
            else:
                status = "not_approved_for_condition"
                edge_sources = [
                    {
                        "resource_id": attribute_source,
                        "resource_role": "aggregator_knowledge_source",
                        "source_record_urls": [ kgInfoUrl + line['id'] ]
                    },
                    {
                        "resource_id": faers,
                        "resource_role": "primary_knowledge_source"
                    },
                    {
                        "resource_id": dailymed,
                        "resource_role": "supporting_data_source"
                    }
                ]

            # Yield subject, predicate, and object properties
            data = {
                "status": status,
                "disease": disease,
                "edge_id": line['id'],
                "sources": edge_sources
            }
            
            yield subj, data

        else:
            print(f"Cannot find prefix for {line} !")

def load_data(data_folder):
    output = {}
    final = []
    edges = load_content(data_folder)
    while 1:
        try: subj, entry = next(edges)
        except: break
        if subj in output:
            output[subj].append(entry)
        else:
            output.update({subj: [entry]})
    for key in output:
        final.append({"_id": key, "clinical_approval": output[key]})
    for entry in final:
        yield entry

def main():
    gen = load_data('test')
    while 1:
        try: entry = next(gen)
        except: break
        print(json.dumps(entry, sort_keys=True, indent=2))

if __name__ == '__main__':
    main()
