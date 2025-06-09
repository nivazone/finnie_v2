# Finnie: AI-Powered Financial Document Processing Assistant

Finnie is an intelligent agent that automates the processing of financial documents, particularly bank statements. It uses Large Language Models (LLMs) and web search capabilities to extract, parse, classify, and store financial data in a structured format.

## 🌟 Features

- **Document Processing**

  - PDF text and table extraction
  - Structured data parsing using LLMs
  - Transaction classification with context
  - Web search integration for better understanding

- **Data Management**

  - PostgreSQL database integration
  - Transaction categorization
  - Statement history tracking
  - Data validation and error handling

- **Intelligent Features**
  - Multi-agent architecture (Scribe, Sage, Fallback)
  - Contextual transaction classification
  - Web search for merchant verification
  - Conversational interface

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- OpenAI API key
- Tavily or Serper API key (for web search)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/finnie_v2.git
cd finnie_v2
```

2. Create and activate a virtual environment:

```bash
python -m venv ml-train
source ml-train/bin/activate  # On Windows: ml-train\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key  # or SERPER_API_KEY
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_db_name
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

5. Initialize the database:

```bash
psql -U your_user -d your_db_name -f db/schema.sql
```

### Usage

Run the chat interface:

```bash
python src/main.py
```

## 📁 Project Structure

```
finnie_v2/
├── src/
│   ├── agents/           # Agent implementations (Scribe, Sage, Fallback)
│   ├── tools/            # Processing tools (extraction, parsing, etc.)
│   ├── main.py          # Entry point
│   ├── config.py        # Configuration management
│   ├── dependencies.py  # Dependency injection
│   └── logger.py        # Logging setup
├── db/
│   └── schema.sql       # Database schema
├── requirements.txt     # Python dependencies
└── .env                # Environment variables
```

## 🔄 Workflow

1. **Document Processing**

   - PDF statement is loaded
   - Text and tables are extracted
   - LLM parses into structured JSON

2. **Data Storage**

   - Account information stored
   - Transactions saved with metadata
   - Categories assigned

3. **Analysis**
   - Transaction classification
   - Web search for context
   - Category validation

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the terms of the license included in the repository.

## 🎯 Roadmap

- [x] Conversational Financial Assistant
- [x] Streaming Support
- [x] Conversation Memory
- [ ] Tax deductible transactions report
- [ ] LLM-Based Anomaly Detection
- [ ] Automated Financial Summaries
- [ ] Natural Language Categorization rules
- [x] Tax Deductibility Classification
- [ ] Smart Budgeting Suggestions
- [x] CSV bank statements support
- [ ] Financial Insights Dashboard
