# Finnie: Automated Bank Statement Processing Agent

Finnie is an AI-powered agent that automates the extraction, parsing, classification, and storage of bank statement data. It leverages LLMs and web search to process PDF statements, extract transactions, classify them, and persist results in a PostgreSQL database.

## Features

- **PDF Extraction:** Extracts text and tables from bank statement PDFs.
- **LLM Parsing:** Parses extracted text into structured JSON using an LLM.
- **Database Integration:** Stores parsed statements and transactions in PostgreSQL.
- **Transaction Classification:** Classifies transactions into categories using LLMs and web search context.
- **Error Handling:** Robust error and logging system for traceability.
- **Extensible Tools:** Modular tool system for each processing step.

## Workflow

1. **Extract Text:** Extracts plain text and tables from a PDF statement.
2. **Parse Statement:** Converts extracted text into structured JSON (account info, transactions).
3. **Write to DB:** Saves the structured data into the database.
4. **Read from DB:** Retrieves the latest statement and its transactions.
5. **Classify Transactions:** Uses LLM and web search to classify each transaction.
6. **Update DB:** Updates transaction categories in the database.

## Project Structure

- `src/agent.py` — Orchestrates the agent workflow using a state graph.
- `src/tools/` — Modular tools for extraction, parsing, DB operations, and classification.
- `src/dependencies.py` — Dependency management (LLMs, DB pool, search).
- `src/config.py` — Environment and settings management.
- `db/schema.sql` — PostgreSQL schema for statements and transactions.
- `statements/` — Folder for input PDF statements.

## Requirements

- Python 3.10+
- PostgreSQL
- OpenAI API key (for LLM)
- Tavily API key (for web search)

Install dependencies:

```sh
pip install -r requirements.txt
```

## TODO

- Conversational Financial Assistant
- Add streaming
- Add conversation memory
- LLM-Based Anomaly Detector
- Generate human-readable summaries of monthly/quarterly spending.
- Natural-Language Categorization Rules, Allow user to define logic like: “Put all Uber rides under Transport” or“Flag anything with ‘crypto’ as High Risk”
- Tax Deductibility Classification
- Auto-Budgeting Suggestions
