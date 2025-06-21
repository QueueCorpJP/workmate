# Handling “Unnamed” Columns — Language‑Agnostic Guide  

**Purpose**  
Provide any AI agent with a clear, format‑neutral procedure to detect and fix “Unnamed” or **header‑less** columns that arise during table extraction from CSV, Excel, PDF, or other sources.  
*No programming snippets or hard‑coded column references are included.*

---

## 1. Root Causes  

1. **Empty header cells**: A column header cell is blank in the source table.  
2. **Row index exported as data**: Row numbering is saved as a physical column while its header cell remains blank.  
3. **Decorative first row**: A title or note occupies the top row, causing the real headers to shift downward.  
4. **Partial capture in PDF parsing**: Table borders or text are missed, leaving header cells empty.

In each case the extraction tool assigns a placeholder label such as *Unnamed*, *Column X*, or similar.

---

## 2. Detection Principles  

- **Header integrity scan**  
  - Review the first few rows after extraction.  
  - Flag a row as a *true header* when most cells contain descriptive text and well‑known domain keywords occur together.  
- **Placeholder identification**  
  - Treat any header that is blank or begins with generic tokens (e.g., “Unnamed” or “Column”) as a missing‑name column.  
- **Shift verification**  
  - If the suspected header row is followed by a row with equally descriptive values, assume the header is displaced by one row.

---

## 3. Remediation Flow  

1. **Skip non‑header rows**  
   Ignore rows that are decorative or predominantly empty before selecting the header row.  
2. **Rename or absorb placeholder columns**  
   - If the column stores pure row numbers, convert it into the data index and remove it from the visible table.  
   - If it holds meaningful data, derive an appropriate name from context (for example, by referencing adjacent cells or repeating labels within the column).  
   - If no suitable name can be inferred, mark the column for manual review.  
3. **Propagate clean structure**  
   Save a log of which rows were skipped and how many columns were renamed or removed, ensuring reproducibility.

---

## 4. Implementation Guidelines for AI Agents  

- Operate **format‑agnostically**: apply the same logical steps regardless of whether the table originates from CSV, Excel, or PDF.  
- Use **dynamic thresholds**: determine acceptable proportions of empty cells and keyword matches per file instead of fixed numbers.  
- Prefer **integration over deletion**: keep data by renaming columns when possible; delete only as a last resort once confirmed irrelevant.  
- Produce an **explainable audit trail**: record every header adjustment so downstream processes can verify the transformation.

---

## 5. Recommended Keyword Examples  

Include business‑specific terms that typically appear in header rows (replace with your domain vocabulary):  
- customer number, address, status, date, amount, identifier

Presence of multiple keywords in the same row strongly indicates the row is a genuine header.

---

## 6. Common Pitfalls and Mitigations  

| Pitfall | Mitigation |
|---------|-----------|
| Long runs of empty columns on the right edge | Trim trailing empty columns before processing |
| Multi‑row headers | Concatenate stacked header rows into one row before analysis |
| Mixed languages | Maintain a multilingual keyword list or perform language detection before scanning |

---

**End of Guide**
