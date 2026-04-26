# Structural Heart Disease Paper Search & Download Project

## Task

Build a comprehensive library of landmark and important papers in structural heart
disease — covering transcatheter AND surgical approaches to the aortic, mitral, and
tricuspid valves. This uses two search strategies: (1) author-based search targeting
key researchers, and (2) topic-based search targeting landmark trials and important
clinical questions. Download every freely available PDF to a local folder.

## Output Folder

Save all downloaded PDFs to: `knowledge/papers/inbox/`

An automated indexer will rename, catalog, and integrate them into the knowledge base.
You do not need to worry about final file naming — just get the PDFs into the inbox.

---

## Search Strategy 1: Key Authors

Search PubMed for all papers authored by the researchers listed below, published in
the specified journals from 2005 to the present.

### Authors — Transcatheter / Interventional

1. Michael J. Mack, M.D. (Mack MJ)
2. Martin B. Leon, M.D. (Leon MB)
3. Vinod H. Thourani, M.D. (Thourani VH)
4. Raj Makkar, M.D. (Makkar R, Makkar RR)
5. Susheel K. Kodali, M.D. (Kodali SK)
6. Rebecca T. Hahn, M.D. (Hahn RT)
7. Philippe Genereux, M.D. (Genereux P)
8. Craig R. Smith, M.D. (Smith CR)
9. Megan Coylewright, M.D. (Coylewright M)
10. John K. Forrest, M.D. (Forrest JK)
11. G. Michael Deeb, M.D. (Deeb GM)
12. Michael J. Reardon, M.D. (Reardon MJ)
13. Gregg W. Stone, M.D. (Stone GW)
14. Paul Sorajja, M.D. (Sorajja P)
15. Ted Feldman, M.D. (Feldman T)
16. Lars Sondergaard, M.D. (Sondergaard L)

### Authors — Surgical / Critical Voices

17. [author redacted per pen name]
18. Vinay Badhwar, M.D. (Badhwar V)
19. J. Hunter Mehaffey, M.D. (Mehaffey JH)
20. Sanjay Kaul, M.D. (Kaul S)
21. D. Craig Miller, M.D. (Miller DC)
22. Joanna Chikwe, M.D. (Chikwe J)
23. Joseph E. Bavaria, M.D. (Bavaria JE)
24. Michael A. Borger, M.D. (Borger MA)
25. Thierry Mesana, M.D. (Mesana T)
26. Marc R. Moon, M.D. (Moon MR)
27. Rakesh M. Suri, M.D. (Suri RM)

### Matching Rule

Find papers where **any** of the listed authors appears (not requiring co-authorship).

---

## Search Strategy 2: Topic-Based Search

In addition to author searches, run the following topic-based PubMed queries across
all listed journals. These capture landmark trials and important topics regardless
of author.

### Landmark Trial Names (search title/abstract)
```
("PARTNER" OR "COAPT" OR "MITRA-FR" OR "TRILUMINATE" OR "TRISCEND" OR
"CLASP" OR "SURTAVI" OR "CoreValve" OR "NOTION" OR "DEDICATE" OR
"EARLY TAVR" OR "EVOLVED" OR "SAPIEN" OR "RECOVERY" OR "AVATAR" OR
"REPRISE" OR "PROTECTED TAVR" OR "ENVISAGE" OR "UK TAVI" OR
"APOLLO" OR "ACURATE" OR "FORWARD" OR "UNLOAD")
```

### Key Topic Queries
Run each of these as separate searches:

1. **Aortic — transcatheter vs surgical:**
   `("TAVR" OR "TAVI" OR "transcatheter aortic") AND ("surgical" OR "SAVR") AND ("comparison" OR "outcomes" OR "randomized")`

2. **Aortic — bicuspid:**
   `("bicuspid" OR "BAV") AND ("TAVR" OR "TAVI" OR "aortic valve replacement")`

3. **Aortic — low risk:**
   `("low risk" OR "low-risk") AND ("TAVR" OR "TAVI") AND ("aortic stenosis")`

4. **Mitral — transcatheter repair:**
   `("MitraClip" OR "PASCAL" OR "transcatheter mitral" OR "TEER" OR "edge-to-edge") AND ("mitral regurgitation")`

5. **Mitral — surgical repair vs replacement:**
   `("mitral valve repair" OR "mitral valve replacement") AND ("outcomes" OR "randomized" OR "comparison")`

6. **Tricuspid — transcatheter:**
   `("TriClip" OR "PASCAL" OR "transcatheter tricuspid" OR "TTVR" OR "tricuspid TEER") AND ("tricuspid regurgitation")`

7. **Tricuspid — surgical:**
   `("tricuspid valve surgery" OR "tricuspid annuloplasty" OR "tricuspid repair") AND ("outcomes")`

8. **Durability / long-term:**
   `("structural valve deterioration" OR "SVD" OR "bioprosthetic" OR "durability" OR "long-term") AND ("TAVR" OR "TAVI" OR "transcatheter")`

9. **Guidelines / consensus:**
   `("guideline" OR "consensus" OR "expert consensus" OR "appropriate use") AND ("valvular heart disease" OR "aortic stenosis" OR "mitral regurgitation" OR "tricuspid")`

10. **Surgical outcomes / STS database:**
    `("STS database" OR "STS registry" OR "surgical outcomes") AND ("aortic valve" OR "mitral valve" OR "tricuspid valve")`

---

## Journals

### Tier 1 (highest priority — download everything)
- New England Journal of Medicine (`N Engl J Med`)
- JAMA (`JAMA`)
- JAMA Cardiology (`JAMA Cardiol`)
- The Lancet (`Lancet`)
- Journal of the American College of Cardiology (`J Am Coll Cardiol`)

### Tier 2 (high priority)
- European Heart Journal (`Eur Heart J`)
- Circulation (`Circulation`)
- JACC: Cardiovascular Interventions (`JACC Cardiovasc Interv`)

### Tier 3 (surgical journals — important for comparative data)
- Annals of Thoracic Surgery (`Ann Thorac Surg`)
- Journal of Thoracic and Cardiovascular Surgery (`J Thorac Cardiovasc Surg`)
- European Journal of Cardio-Thoracic Surgery (`Eur J Cardiothorac Surg`)

## Date Range

2005 – present

---

## Step-by-Step Instructions

### 1. Search PubMed

Use the NCBI PubMed E-utilities API (or browser-based PubMed search).

**For author searches**, query each author across all journals:
```
"{Author Initials}"[Author] AND ("{Journal1}"[Journal] OR "{Journal2}"[Journal] OR ...) AND 2005:2026[dp]
```

**For topic searches**, query across all journals:
```
({topic query}) AND ("{Journal1}"[Journal] OR "{Journal2}"[Journal] OR ...) AND 2005:2026[dp]
```

Deduplicate all results by PMID across all searches.

### 2. Fetch Article Metadata

For all unique PMIDs, retrieve:
- PMID
- Title
- Journal name
- Publication date (year, month)
- Full author list
- DOI
- PMC ID (if available — indicates free full text on PubMed Central)

### 3. Identify Freely Available PDFs

A paper likely has a free PDF if:
- It has a **PMC ID** (available via `https://www.ncbi.nlm.nih.gov/pmc/articles/{PMC_ID}/pdf/`)
- The journal provides open access (some NEJM and Lancet articles become free after embargo)
- The DOI resolves to a page with a free PDF download link
- **If you have institutional access**, download the PDF directly from the publisher

Check PMC availability first. Then try the publisher page via DOI.

### 4. Download PDFs

For each available paper:
- Download the PDF
- Name the file: `{Year}_{FirstAuthorLastName}_{Journal}_{PMID}.pdf`
  - Example: `2019_Mack_NEJM_30883058.pdf`
- Save all PDFs to: **`knowledge/papers/inbox/`**

### 5. Create Master Spreadsheet

Create an Excel file (`Structural_Heart_Papers_Master_List.xlsx`) with columns:
- PMID
- Title
- Journal
- Publication Date
- First Author
- Full Author List
- DOI
- PMC ID
- PDF Available (Yes/No)
- PDF Downloaded (Yes/No)
- PDF Filename
- PubMed URL (`https://pubmed.ncbi.nlm.nih.gov/{PMID}/`)
- DOI URL (`https://doi.org/{DOI}`)
- Search Source (Author / Topic / Both)

Sort by Journal tier, then by Publication Date (newest first).

Include a summary sheet with:
- Total papers found per author
- Total papers found per journal
- Total papers found per topic search
- Total PDFs downloaded vs. total papers

### 6. Output

Save everything to:
- All PDFs → `knowledge/papers/inbox/`
- Spreadsheet → `knowledge/Structural_Heart_Papers_Master_List.xlsx`

The automated indexer will process the inbox PDFs, extract metadata using AI,
rename them descriptively, and add them to the knowledge base.

---

## Requirements

- **Institutional access recommended**: Running this from a hospital/university computer
  with journal subscriptions will dramatically increase the number of downloadable PDFs
- **Browser access needed**: Chrome (or another browser) for PubMed access and PDF downloads
- **Expected volume**: Likely 500–1500+ unique papers across all authors, topics, and journals
- **Be thorough**: Many papers will appear in multiple searches — deduplicate by PMID
- **Prioritize downloads**: If time-limited, prioritize Tier 1 journals and landmark trials

## Notes for Reuse

To adapt this for a different specialty:
1. Update the **Authors** list and PubMed name formats
2. Update the **Topic queries** for the relevant clinical domain
3. Update the **Journals** list and tiers
4. Adjust the **Date Range** as needed
5. Run the same workflow — the indexer handles the rest
