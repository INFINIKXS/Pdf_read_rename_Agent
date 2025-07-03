# How to Use the Document Intelligence Agent

## 1. Prepare Your Source Files
- Place all your source PDF files in the `pdfs` folder in the project root.

## 2. Rename Your Files
- Start the renaming process by running:
  ```
  python main.py rename
  ```
- The tool will prompt you for the source (`pdfs`) and destination (e.g., `renamed`) folders.
- After renaming, check the `Error` subfolder inside your destination folder for any files that failed to process. You can retry these files by moving them back to the `pdfs` folder and running the rename process again.

## 3. Add Your Research Details
- Open or create the `research_details.md` file in the project root.
- Fill in your research topic, aim, questions, objectives, and rationale. This information will be used to guide the research paper selection process.

## 4. Start the Research Paper Selection Process
- Run:
  ```
  python main.py research
  ```
- The tool will prompt you for the source (e.g., `renamed`) and destination (e.g., `chosen`) folders.
- The agent will use your research details to select relevant papers.
- Check the `Error` subfolder inside your destination folder for any files that failed to process. You can retry these files by moving them back to the source folder and running the process again.

## 5. Review Your Results
- Access the `chosen` folder for the selected, relevant files.
- For more details on why and how papers were chosen, review the `reason_for_paper_selection.md` file generated in the project root. This file contains the LLM's justifications and selection scores for each paper.

---

**Tip:** Always check the `Error` folders after each step to ensure no files are missed. You can retry failed files as needed.
