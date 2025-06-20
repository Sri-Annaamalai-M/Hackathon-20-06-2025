# Agentic AI-Powered Role Matching & Offer Recommendation Engine

An end-to-end AI-powered system that autonomously analyzes candidate profiles, matches them to open roles, suggests optimized offer packages, and provides explainable recommendations for HR decision-making.

## Project Overview

This system uses a multi-agent architecture powered by Google's Gemini AI to create an intelligent role matching and offer recommendation engine. The entire system is built with MongoDB for data storage and SentenceTransformer for embedding generation, making it easy to set up and run.

### Key Features

- **AI-Powered Resume Parsing**: Automatically extracts structured information from resumes and interview notes
- **Semantic Role Matching**: Uses vector embeddings to match candidates to roles based on skills, experience, and preferences
- **Personalized Offer Generation**: Creates tailored offer packages based on candidate qualifications and market data
- **Explainable Recommendations**: Provides clear explanations for all matches and offers
- **Feedback-Driven Improvement**: Learns from HR feedback to improve future recommendations

## System Architecture

### Tech Stack

- **Frontend**: React.js with Vite, Material UI
- **Backend**: Python FastAPI
- **Database**: MongoDB (for both structured data and vector embeddings)
- **AI Components**: Google Gemini, SentenceTransformer
- **Agent Orchestration**: Custom multi-agent system

### Agentic AI Components

1. **Profile Parser Agent**: Processes resumes to extract structured candidate profiles
2. **Role Matching Agent**: Matches candidates to roles using vector similarity and AI reasoning
3. **Offer Recommendation Agent**: Generates personalized offer packages
4. **Explanation Generator Agent**: Creates human-readable justifications
5. **Feedback Processor Agent**: Analyzes HR feedback to improve the system
6. **Blacklist Agent**: Filters out candidates who don't meet minimum requirements

## Getting Started

### Prerequisites

- Python 3.8+ with venv
- Node.js and npm
- MongoDB (local or Atlas)
- Google Gemini API key

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-role-matcher.git
   cd ai-role-matcher-backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn motor pymongo python-multipart python-dotenv pydantic email-validator httpx langchain langchain-google-genai google-generativeai sentence-transformers numpy pandas pypdf docx2txt pillow
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```
   # MongoDB settings
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB_NAME=role_matcher_db

   # Google Gemini settings
   GOOGLE_API_KEY=your_gemini_api_key_here

   # File upload settings
   UPLOAD_DIR=uploads

   # Security settings
   SECRET_KEY=your_secret_key_here
   ```

5. **Initialize MongoDB with sample data**
   ```bash
   python setup_mongodb.py
   ```

6. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../ai-role-matcher
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

## Usage Guide

### Uploading Candidates

1. Navigate to the "Upload Candidates" page
2. Drag and drop resume files (PDF or DOCX)
3. Click "Upload" to process the files
4. The AI agent will extract structured candidate profiles

### Matching Candidates to Roles

1. Go to the "Role Matching" page
2. Click "Run Matching Process" to match candidates to roles
3. View match details, including match scores and explanations
4. Filter and sort matches based on various criteria

### Managing Offer Recommendations

1. Navigate to the "Offer Recommendations" page
2. Select a match to generate an offer
3. Review AI-generated offer packages
4. Modify offers if needed
5. Approve or reject offers

### Providing Feedback

1. Review matches and offers
2. Provide feedback on recommendations
3. The system will learn from your feedback to improve future recommendations

## Development

### Project Structure

```
ai-role-matching-system/
├── ai-role-matcher/               # Frontend
│   ├── public/
│   ├── src/
│   │   ├── components/            # Reusable UI components
│   │   ├── pages/                 # Main application pages
│   │   ├── App.jsx                # Main application component
│   │   └── main.jsx               # Entry point
│   ├── package.json
│   └── vite.config.js
│
└── ai-role-matcher-backend/       # Backend
    ├── app/
    │   ├── agents/                # AI agents
    │   │   ├── profile_parser.py  # Resume parsing agent
    │   │   ├── role_matcher.py    # Role matching agent
    │   │   ├── offer_recommender.py  # Offer recommendation agent
    │   │   ├── explanation_generator.py  # Explanation generation agent
    │   │   ├── feedback_processor.py  # Feedback processing agent
    │   │   └── blacklist_agent.py  # Candidate filtering agent
    │   ├── api/                   # API routes
    │   │   └── routes/
    │   ├── core/                  # Core functionality
    │   │   └── config.py          # Configuration settings
    │   ├── db/                    # Database connections
    │   │   ├── mongodb.py         # MongoDB connection
    │   │   └── vector_store.py    # Vector store implementation
    │   ├── schemas/               # Data models
    │   │   └── models.py          # Pydantic models
    │   └── main.py                # Application entry point
    ├── uploads/                   # File upload directory
    │   ├── resumes/
    │   └── notes/
    ├── setup_mongodb.py           # Database initialization script
    └── requirements.txt           # Python dependencies
```

### Extending the System

1. **Adding New Agent Types**
   - Create a new agent class in the `app/agents` directory
   - Follow the existing pattern for agent initialization and execution

2. **Customizing Matching Logic**
   - Modify the `role_matcher.py` file to adjust matching criteria
   - Update the prompts to change how matches are evaluated

3. **Enhancing Offer Generation**
   - Edit the `offer_recommender.py` file to customize offer generation
   - Adjust the market data analysis for different compensation strategies

## Production Deployment

For production deployment, consider:

1. **Scaling the Database**
   - Use MongoDB Atlas for a managed database solution
   - Consider implementing MongoDB Atlas Vector Search for more efficient vector operations

2. **Securing the Application**
   - Implement proper authentication and authorization
   - Restrict CORS to specific origins
   - Use environment-specific configuration

3. **Performance Optimization**
   - Add caching for frequent operations
   - Implement background processing for long-running tasks

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for powering the intelligent agents
- SentenceTransformer for embedding generation
- MongoDB for providing flexible data storage

- ![image](https://github.com/user-attachments/assets/bc286cba-2f92-44c1-9336-f1f4b04b7949)
