"""Pfam v3: batch-search strategy. 50 accessions per search query, 500-accession
URL stays under UniProt's ~8KB limit. Approximately 500 requests, 1 sec each,
~10 min wall. Uses the same /uniprotkb/search endpoint that v1 failed on at
500/batch; reducing to 50/batch keeps URL size manageable."""
import json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

SRC = Path(r"C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2\_data\data_25k\experiment2_proteins_25k_filtered.json")
DST = Path(r"C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2\_data\data_25k\experiment2_proteins_25k_pfam_v3.json")
LOG = Path(r"C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2\_experiments\homology_cliff\logs\pfam_v3.log")
LOG.parent.mkdir(parents=True, exist_ok=True)

def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line)
    with open(LOG, 'a') as f: f.write(line + "\n")

with open(SRC, 'r', encoding='utf-8') as f:
    doc = json.load(f)
entries = doc['test_set']
accs = [e['uniprot_acc'] for e in entries]
log(f"loaded {len(accs)} accs")

BATCH = 50
FIELDS = "accession,xref_pfam,organism_name,organism_id,lineage"
BASE = "https://rest.uniprot.org/uniprotkb/search"

augmented = {}
for i in range(0, len(accs), BATCH):
    batch = accs[i:i+BATCH]
    q = "(" + " OR ".join(f"accession:{a}" for a in batch) + ")"
    params = urllib.parse.urlencode({"query": q, "fields": FIELDS, "format": "json", "size": BATCH})
    url = BASE + "?" + params
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        for hit in data.get("results", []):
            acc = hit.get("primaryAccession")
            pfam = [x["id"] for x in hit.get("uniProtKBCrossReferences", []) if x.get("database") == "Pfam"]
            org = hit.get("organism", {})
            augmented[acc] = {
                "pfam_ids": pfam,
                "organism": org.get("scientificName", ""),
                "taxonomy_id": org.get("taxonId", 0),
                "lineage": org.get("lineage", []),
            }
        if (i // BATCH) % 25 == 0:
            log(f"batch {i//BATCH+1}/{(len(accs)+BATCH-1)//BATCH}: total={len(augmented)}")
    except urllib.error.HTTPError as e:
        log(f"batch {i//BATCH+1} HTTP {e.code}")
    except Exception as e:
        log(f"batch {i//BATCH+1} ERR: {e}")
    time.sleep(0.4)

for e in entries:
    a = e["uniprot_acc"]
    if a in augmented:
        e.update(augmented[a])
    else:
        e["pfam_ids"] = []; e["organism"] = ""; e["taxonomy_id"] = 0; e["lineage"] = []
doc["test_set"] = entries
doc["pfam_v3_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(DST, "w", encoding="utf-8") as f:
    json.dump(doc, f)
log(f"wrote {DST}")
log(f"coverage: {sum(1 for e in entries if e.get('pfam_ids'))}/{len(entries)} have Pfam IDs")
