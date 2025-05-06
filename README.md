# Generative AI Job Advisor

A comprehensive career assistant platform powered by AI to help users with job interviews, resume analysis, and career path recommendations.

## 🌟 Features

- **Mock Interview Practice**: Generate realistic interview questions based on job titles and receive AI-powered critiques of your answers
- **Resume Analysis**: Upload your resume for AI-powered analysis and improvement suggestions
- **Career Path Recommendations**: Get personalized career path recommendations based on your resume
- **User Authentication**: Secure login and signup functionality via Supabase

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Database**: Supabase (PostgreSQL with pgvector extension)
- **AI**: Groq API (mixtral-8x7b-32768 model)
- **Vector Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)

## 🔍 RAG (Retrieval-Augmented Generation)

The app uses pgvector + SentenceTransformers to index job descriptions and retrieve similar jobs at runtime.

Used in:
- `/interview/question`: Contextual question generation
- Future: Personalization of recommendations

Embedding model: `all-MiniLM-L6-v2`  
Vector dim: 384

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Supabase account
- Groq API key

### Environment Setup

1. Clone the repository
2. Create a `.env` file based on `.env.example`:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama3-70b-8192
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

1. Start the FastAPI backend:

```bash
cd app
uvicorn main:app --reload
```

2. Start the Streamlit frontend:

```bash
cd streamlit_app
streamlit run main.py
```

## 📚 API Endpoints

### Health
- `GET /health`: Check API health

### Resume
- `POST /resume/upload`: Upload and parse a resume PDF

### Career
- `POST /career/recommend`: Get career path recommendations based on resume

### Interview
- `POST /interview/question`: Generate interview questions for a job title
- `POST /interview/critique`: Get AI critique of interview answers

## 📁 Project Structure

The following outlines the folder and file organization of this project:

```
.
├── .env.example
├── .gitignore
├── README.md
├── app/
│   ├── __pycache__/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── deps.py
│   │   └── endpoints/
│   ├── core/
│   │   └── __init__.py
│   ├── main.py
│   ├── models/
│   │   └── __init__.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── loader.py
│   │   ├── mock_critique.md
│   │   ├── mock_question.md
│   │   └── rag_enhanced_question.md
│   └── services/
│       ├── __init__.py
│       ├── __pycache__/
│       ├── db_ops.py
│       ├── embeddings.py
│       ├── groq_service.py
│       ├── pdf_parser.py
│       ├── supabase_client.py
│       └── vector_seach.py
├── infra/
│   └── .placeholder
├── requirements.txt
├── streamlit_app/
│   └── main.py
└── tests/
    ├── test_groq.py
    └── test_health.py
```

This structure helps contributors and users quickly understand the layout and main components of the codebase.

## 🧪 Testing

Run tests using pytest:

```bash
python -m pytest
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
