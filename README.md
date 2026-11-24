# 📚 FLIPBOOK-AI
### AI-Powered Document Reading, Research & Learning Platform

**FLIPBOOK-AI** is an AI-powered document management and learning platform designed to transform static PDF documents into interactive reading, research, and learning experiences.

The platform combines PDF processing, AI-powered document conversations, Retrieval-Augmented Generation (RAG), quizzes, and flashcards in one workspace.

---

## ✨ Features

### 📖 Document Management & Reading
- Upload and manage PDF documents.
- Process and extract PDF content.
- Interactive PDF reading experience.
- Document library management.

### 🤖 AI Research Assistant
- Chat with uploaded PDF documents.
- Ask questions about document content.
- Context-aware responses using Retrieval-Augmented Generation (RAG).
- Semantic document retrieval.

### 🎓 AI Learning Studio
- Generate quizzes from uploaded documents.
- Take interactive quizzes.
- View quiz results and scores.
- Generate and review flashcards.

### 🔐 Authentication
- User registration and login.
- Protected application routes.
- JWT-based authentication.

### 🧠 AI & Document Processing
- PDF text extraction.
- Text chunking and embeddings.
- Vector database integration.
- Local language model integration.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS |
| Backend | Python, Flask |
| Database | SQLAlchemy |
| AI Framework | LangChain |
| Language Model | Ollama, Llama 3.2 |
| Embeddings | Nomic Embed Text |
| Vector Database | ChromaDB |
| PDF Processing | PyMuPDF, Poppler, pdf2image |
| Authentication | JWT |
| Version Control | Git, GitHub |

---

## 🏗️ Project Architecture

```text
FLIPBOOK-AI/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── assistant/
│   │   │   ├── auth/
│   │   │   ├── learning/
│   │   │   ├── library/
│   │   │   └── reader/
│   │   ├── services/
│   │   ├── stores/
│   │   └── styles/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   └── run.py
│
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites

Install the following:

- Python 3.11+
- Node.js and npm
- Git
- Ollama
- Poppler (for PDF processing)

### 1. Clone the Repository

```bash
git clone https://github.com/singhshagun08/FLIPBOOK-AI.git
cd FLIPBOOK-AI
```

### 2. Backend Setup

Open a terminal:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables using your local configuration and `.env` file. Never commit your secrets.

Start the backend:

```bash
python run.py
```

### 3. AI Model Setup

Install Ollama and download the models:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

Ensure the Ollama service is running and the backend configuration points to the installed models.

### 4. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

---

## 🔄 Application Workflow

1. Register or log in to the platform.
2. Upload a PDF document.
3. Extract and process document content.
4. Generate embeddings and store document representations.
5. Ask questions using the AI Research Assistant.
6. Generate quizzes and flashcards.
7. Read, learn, and explore document information.

---

## 🚧 Development Status

FLIPBOOK-AI is under active development.

Implemented areas include authentication, PDF upload and reading, AI-powered document conversations, quiz generation, quiz evaluation, and flashcards.

Research, Notebook, Audiobook, Translation, Analytics, and Settings are planned areas whose full functionality is still being developed.

---

## 🔮 Future Enhancements

- AI-powered audiobook generation.
- Multilingual document translation.
- Advanced research workspace.
- Smart note-taking.
- Learning analytics dashboard.
- Improved document organization.
- Production deployment and scalability.

---

## 👩‍💻 Creator

**Shagun Singh**

Creator and Developer of FLIPBOOK-AI.

B.Tech Computer Science & Engineering

---

## 📄 License

This project is currently developed as an independent project. Licensing terms can be added when a license is selected.
