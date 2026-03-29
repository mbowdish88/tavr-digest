# TAVR Paper Search & Download Project

## Task

Search PubMed for all papers authored by the researchers listed below, published in the specified journals from 2005 to the present. Compile a master list of every paper found, then download every freely available PDF to a local folder.

## Authors

1. Michael J. Mack, M.D.
2. Martin B. Leon, M.D.
3. Vinod H. Thourani, M.D.
4. Raj Makkar, M.D.
5. Susheel K. Kodali, M.D.
6. Rebecca T. Hahn, M.D.
7. Philippe Genereux, M.D.
8. Craig R. Smith, M.D.
9. Megan Coylewright, MD, MPH
10. John K. Forrest, MD
11. G. Michael Deeb, MD
12. Michael J. Reardon, MD

## Journals

- New England Journal of Medicine (NEJM)
- JAMA
- JAMA Cardiology
- The Lancet
- Journal of the American College of Cardiology (JACC)

## Date Range

2005 – present

## Matching Rule

Find papers where **any** of the listed authors appears (not requiring co-authorship among them).

## Step-by-Step Instructions

### 1. Search PubMed

Use the NCBI PubMed E-utilities API (or browser-based PubMed search) to query each author across all five journals. The PubMed search query format for each author should be:

```
"{Author Initials}"[Author] AND ("{Journal1}"[Journal] OR "{Journal2}"[Journal] OR ...) AND 2005:2026[dp]
```

**PubMed author name formats to use:**
- Mack MJ
- Leon MB
- Thourani VH
- Makkar R (also try Makkar RR)
- Kodali SK
- Hahn RT
- Genereux P
- Smith CR
- Coylewright M
- Forrest JK
- Deeb GM
- Reardon MJ

**PubMed journal abbreviations:**
- `N Engl J Med`
- `JAMA`
- `JAMA Cardiol`
- `Lancet`
- `J Am Coll Cardiol`

Deduplicate results by PMID across all author searches.

### 2. Fetch Article Metadata

For all unique PMIDs, use PubMed's efetch API (or scrape the PubMed pages) to retrieve:
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
- The journal provides open access (e.g., some NEJM and Lancet articles become free after embargo)
- The DOI resolves to a page with a free PDF download link

Check each article for PMC availability first. For articles without PMC IDs, attempt to access the publisher page via DOI to check for open-access PDFs.

### 4. Download PDFs

For each freely available paper:
- Download the PDF
- Name the file: `{Year}_{FirstAuthorLastName}_{Journal}_{PMID}.pdf`
  - Example: `2019_Mack_NEJM_30883058.pdf`
- Save all PDFs to the designated output folder

### 5. Create Master Spreadsheet

Create an Excel file (`TAVR_Papers_Master_List.xlsx`) with the following columns:
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

Sort by Journal, then by Publication Date (newest first).

Include a summary sheet with:
- Total papers found per author
- Total papers found per journal
- Total PDFs downloaded vs. total papers

### 6. Output

Save everything to the user's selected folder:
- All downloaded PDFs
- `TAVR_Papers_Master_List.xlsx`

## Requirements

- **Browser access needed**: Chrome (or another browser with Claude extension) must be connected for PubMed API access and PDF downloads
- **Expected volume**: Likely 200–500+ unique papers across all authors and journals
- **Be thorough**: These authors are prolific TAVR researchers who frequently co-author together. Many papers will appear in multiple author searches — deduplicate carefully.

## Notes for Reuse

To adapt this for different authors or journals:
1. Update the **Authors** list and their PubMed name formats
2. Update the **Journals** list and their PubMed abbreviations
3. Adjust the **Date Range** as needed
4. Run the same workflow
