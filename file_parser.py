import pandas as pd
import os
import json

attribute_source = "infores:biothings-multiomics-drugapprovals"
attribute_data_source = "infores:isb-wellness"
faers = "infores:faers"
dailymed = "infores:dailymed"
kgInfoUrl = "https://db.systemsbiology.net/gestalt/cgi-pub/KGinfo.pl?id="

def load_data(data_folder):
    edges_file_path = os.path.join(data_folder, "drug_approvals_kg_edges_v0.1.tsv")
    nodes_file_path = os.path.join(data_folder, "drug_approvals_kg_nodes_v0.1.tsv")

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

            prefix = subj.split(':')[0].replace(".","_")
            subject = {
                "id": subj,
                prefix.lower(): subj,
                "name": id_name_mapping[subj],
                "type": id_type_mapping[subj]
            }

            prefix = obj.split(':')[0].replace(".","_")
            object_ = {
                "id": obj,
                prefix.lower(): obj,
                "name": id_name_mapping[obj],
                "type": id_type_mapping[obj]
            }

            # properties for predicate/association
            edge_attributes = []

            # knowledge level
            edge_attributes.append(
                {
                    "attribute_type_id": "biolink:knowledge_level",
                    "value": line['knowledge_level'],
                }
            )

            # agent type
            edge_attributes.append(
                {
                    "attribute_type_id": "biolink:agent_type",
                     "value": line['agent_type'],
                }
            )

            # approval status
            edge_attributes.append(
                {
                    "attribute_type_id": "clinical_approval_status",
                    "value": "approved_for_condition" if pred=="treats" else "not_approved_for_condition",
                 }
            )

            # approval NDAs
            #edge_attributes.append(
            #    {
            #        "attribute_type_id": "approvals",
            #        "value": line['approval'],
            #     }
            #)

            # supporting SPLs
            #edge_attributes.append(
            #    {
            #        "attribute_type_id": "supporting SPLs",
            #        "value": line['supporting_spls'],
            #     }
            #)

            # sources
            edge_sources = [
                {
                    "resource_id": attribute_source,
                    "resource_role": "aggregator_knowledge_source",
                    "source_record_urls": [ kgInfoUrl + line['rowId'] ]
                },
                {
                    "resource_id": dailymed if pred == 'treats' else faers,
                    "resource_role": "primary_knowledge_source"
                },
                {
                    "resource_id": faers if pred == 'treats' else dailymed,
                    "resource_role": "supporting_data_source"
                }
            ]

            association = {
                "label": pred,
                "attributes": edge_attributes,
                "sources": edge_sources
            }

            # Yield subject, predicate, and object properties
            data = {
                "_id": line['rowId'],
                "subject": subject,
                "association": association,
                "object": object_
            }
            yield data

        else:
            print(f"Cannot find prefix for {line} !")



def main():
    testing = False #True
    done = 0
    gen = load_data('test')
    while not testing or done < 10:
        try: entry = next(gen)
        except:
            break
        else:
            print(json.dumps(entry, sort_keys=True, indent=2))
            done = done + 1
    #print(done)

if __name__ == '__main__':
    main()
