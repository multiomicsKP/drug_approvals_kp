import glob
import gzip
import os
import json

kgInfoUrl = "https://db.systemsbiology.net/gestalt/cgi-pub/KGinfo.pl?id="

def find_file(data_folder, kind):
    matches = sorted(glob.glob(os.path.join(data_folder, f"drug_approvals_kg_{kind}_current.jsonl*")))
    if not matches:
        raise FileNotFoundError(f"No drug_approvals_kg_{kind}*.jsonl* file in {data_folder}")
    return matches[-1]

def open_file(path):
    return gzip.open(path, 'rt') if path.endswith('.gz') else open(path)

def load_content(data_folder):
    edges_file_path = find_file(data_folder, "edges")
    nodes_file_path = find_file(data_folder, "nodes")

    id_name_mapping = {}
    with open_file(nodes_file_path) as nodes_data:
        for row in nodes_data:
            row = json.loads(row)
            id_name_mapping[row["id"]] = row["name"]

    with open_file(edges_file_path) as edges_data:
        for line in edges_data:
            line = json.loads(line)
            subj = line['subject']
            pred = line['predicate']
            obj  = line['object']
            if subj and pred and subj.split(':')[0] and obj.split(':')[0]:
                source_record_url = kgInfoUrl + line['id']
                prefix = obj.split(':')[0].replace(".","_")
                disease = {
                    prefix.lower(): obj,
                    "name": id_name_mapping.get(obj) or line.get("object_name"),
                }

                # Yield subject, predicate, and object properties
                data = {
                    "disease": disease,
                    "edge_id": line['id'],
                    "source_record_urls": [ source_record_url ]
                }

                # approval status, as asserted by the KG; absent for most contraindications
                status = line.get('clinical_approval_status')
                if status is not None:
                    data["status"] = status

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
