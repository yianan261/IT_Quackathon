from typing import List, Dict, Optional, Any
import logging
import os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader, 
    PyPDFLoader,
    UnstructuredMarkdownLoader
)
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service for Stevens Institute information.
    Handles document ingestion, vector storage, and retrieval.
    """

    def __init__(self):
        self.vector_db_path = settings.VECTOR_DB_PATH
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.top_k = settings.RAG_TOP_K
        
        # Use OpenAI embeddings to avoid lzma dependency issues
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize or load vector database
        self.vector_db = self._initialize_vector_db()
        self.retriever = self.vector_db.as_retriever(
            search_kwargs={"k": self.top_k}
        )
        
        logger.info(f"✅ RAG Service initialized with {len(self.vector_db._collection.get()['ids'])} documents")

    def _initialize_vector_db(self) -> Chroma:
        """Initialize ChromaDB vector database"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # Initialize ChromaDB
            vector_db = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings,
                collection_name="stevens_knowledge"
            )
            
            # If database is empty, load initial documents
            if len(vector_db._collection.get()['ids']) == 0:
                logger.info("Empty vector database detected. Loading initial documents...")
                self._load_initial_documents(vector_db)
            
            return vector_db
            
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            raise

    def _load_initial_documents(self, vector_db: Chroma) -> None:
        """Load initial Stevens-specific documents"""
        try:
            # Create sample Stevens documents
            initial_docs = self._create_sample_stevens_docs()
            
            if initial_docs:
                # Split documents into chunks
                chunks = self.text_splitter.split_documents(initial_docs)
                
                # Add to vector database
                vector_db.add_documents(chunks)
                logger.info(f"Added {len(chunks)} document chunks to vector database")
            
        except Exception as e:
            logger.error(f"Error loading initial documents: {str(e)}")

    def _create_sample_stevens_docs(self) -> List[Document]:
        """Create sample Stevens-specific documents for the knowledge base"""
        sample_docs = [
            Document(
                page_content="""
Stevens Institute of Technology Academic Calendar 2024-2025

Fall Semester 2024:
- Classes Begin: September 3, 2024
- Add/Drop Period: September 3-10, 2024
- Thanksgiving Break: November 28-29, 2024
- Last Day of Classes: December 13, 2024
- Final Exams: December 16-20, 2024

Spring Semester 2025:
- Classes Begin: January 21, 2025
- Add/Drop Period: January 21-28, 2025
- Spring Break: March 10-14, 2025
- Last Day of Classes: May 9, 2025
- Final Exams: May 12-16, 2025

Summer Sessions:
- Session I: May 27 - July 3, 2025
- Session II: July 7 - August 13, 2025
                """,
                metadata={
                    "source": "academic_calendar",
                    "type": "calendar",
                    "category": "academic"
                }
            ),
            Document(
                page_content="""
Stevens Institute of Technology Computer Science Program Requirements

Bachelor of Science in Computer Science:
Core Requirements (60 credits):
- CS 115: Introduction to Computer Science
- CS 135: Discrete Structures
- CS 284: Data Structures
- CS 385: Algorithms
- CS 347: Software Engineering
- CS 392: Systems Programming
- CS 496: Principles of Programming Languages

Mathematics Requirements:
- MA 121: Differential Calculus
- MA 122: Integral Calculus
- MA 221: Vector Calculus
- MA 222: Probability and Statistics

Technical Electives:
Students must complete 18 credits of technical electives from approved CS courses at the 300-400 level.

Capstone Project:
- CS 490: Computer Science Senior Design I
- CS 491: Computer Science Senior Design II
                """,
                metadata={
                    "source": "cs_curriculum",
                    "type": "program_requirements",
                    "category": "academic",
                    "program": "computer_science"
                }
            ),
            Document(
                page_content="""
Stevens Institute of Technology Registration and Financial Information

Course Registration:
- Registration opens based on class standing and credit hours
- Seniors register first, followed by juniors, sophomores, and freshmen
- Use Workday Student to register for courses
- Add/drop period is the first week of classes

Tuition and Fees (2024-2025):
- Undergraduate tuition: $58,766 per year
- Graduate tuition: $1,849 per credit hour
- Student activity fee: $400 per semester
- Technology fee: $500 per semester

Payment Deadlines:
- Fall semester: August 15
- Spring semester: January 15
- Summer sessions: One week before session begins

Financial Aid:
- FAFSA deadline: February 15
- Merit scholarships available
- Work-study programs available
- Payment plans available through Nelnet
                """,
                metadata={
                    "source": "registration_financial",
                    "type": "administrative",
                    "category": "financial"
                }
            ),
            Document(
                page_content="""
Stevens Institute of Technology Student Services and Resources

Academic Support:
- Academic Success Center: Tutoring and study skills
- Library: Samuel C. Williams Library with 24/7 study spaces
- Career Center: Resume help, job search, internship placement
- Counseling and Psychological Services (CAPS): Mental health support

Campus Life:
- Student Government Association (SGA)
- Over 100 student organizations and clubs
- Intramural and club sports
- Greek life organizations

Housing:
- On-campus residence halls for undergraduates
- Graduate student housing available
- Meal plans required for residential students

Technology Services:
- Stevens WiFi network campus-wide
- Computer labs in multiple buildings
- IT Help Desk: help@stevens.edu
- Software licensing for students
                """,
                metadata={
                    "source": "student_services",
                    "type": "services",
                    "category": "campus_life"
                }
            ),
            Document(
                page_content="""
Stevens Institute of Technology Faculty and Departments

School of Engineering and Science:
- Computer Science Department
- Electrical and Computer Engineering
- Mechanical Engineering
- Chemical Engineering and Materials Science
- Civil, Environmental and Ocean Engineering
- Mathematical Sciences

School of Business:
- Business Intelligence and Analytics
- Finance
- Information Systems
- Management
- Marketing

School of Systems and Enterprises:
- Systems Engineering
- Engineering Management
- Technology Management

Faculty Contact Information:
- Computer Science Department Chair: Dr. Adriana Compagnoni
- Academic Advising: advising@stevens.edu
- Graduate Admissions: graduate@stevens.edu
- Undergraduate Admissions: admissions@stevens.edu
                """,
                metadata={
                    "source": "faculty_departments",
                    "type": "directory",
                    "category": "academic"
                }
            )
        ]
        
        return sample_docs

    def add_documents(self, documents: List[Document]) -> None:
        """Add new documents to the vector database"""
        try:
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Add to vector database
            self.vector_db.add_documents(chunks)
            
            logger.info(f"Added {len(chunks)} document chunks to vector database")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def add_documents_from_directory(self, directory_path: str) -> None:
        """Load and add documents from a directory"""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                logger.warning(f"Directory {directory_path} does not exist")
                return
            
            # Load different file types
            loaders = []
            
            # Text files
            if list(directory.glob("*.txt")):
                loaders.append(DirectoryLoader(
                    directory_path, 
                    glob="*.txt", 
                    loader_cls=TextLoader
                ))
            
            # PDF files
            if list(directory.glob("*.pdf")):
                loaders.append(DirectoryLoader(
                    directory_path, 
                    glob="*.pdf", 
                    loader_cls=PyPDFLoader
                ))
            
            # Markdown files
            if list(directory.glob("*.md")):
                loaders.append(DirectoryLoader(
                    directory_path, 
                    glob="*.md", 
                    loader_cls=UnstructuredMarkdownLoader
                ))
            
            # Load all documents
            all_documents = []
            for loader in loaders:
                documents = loader.load()
                all_documents.extend(documents)
            
            if all_documents:
                self.add_documents(all_documents)
                logger.info(f"Loaded {len(all_documents)} documents from {directory_path}")
            else:
                logger.info(f"No supported documents found in {directory_path}")
                
        except Exception as e:
            logger.error(f"Error loading documents from directory: {str(e)}")
            raise

    def retrieve_documents(self, query: str, top_k: Optional[int] = None) -> List[Document]:
        """Retrieve relevant documents for a query"""
        try:
            if top_k:
                # Temporarily update retriever
                retriever = self.vector_db.as_retriever(search_kwargs={"k": top_k})
                return retriever.get_relevant_documents(query)
            else:
                return self.retriever.get_relevant_documents(query)
                
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []

    def search_similar(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for similar documents and return with scores"""
        try:
            k = top_k or self.top_k
            results = self.vector_db.similarity_search_with_score(query, k=k)
            
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
                for doc, score in results
            ]
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []

    def get_retriever(self) -> BaseRetriever:
        """Get the retriever for use in chains"""
        return self.retriever

    def delete_collection(self) -> None:
        """Delete the entire collection (use with caution)"""
        try:
            self.vector_db._collection.delete()
            logger.info("Vector database collection deleted")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            collection_data = self.vector_db._collection.get()
            return {
                "total_documents": len(collection_data['ids']),
                "embedding_model": settings.EMBEDDING_MODEL,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)} 