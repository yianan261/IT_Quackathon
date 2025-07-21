#!/usr/bin/env python3
"""
Document Loading Utility for Stevens AI Assistant

This script loads documents from a specified directory and adds them to the
vector database using the RAG service. It supports various file formats
including PDF, TXT, and Markdown files.

Usage:
    python utils/load_documents.py [directory_path]
    
Example:
    python utils/load_documents.py documents/stevens_docs
    python utils/load_documents.py documents/course_materials
"""

import os
import sys
import logging
from pathlib import Path
import argparse
from typing import Optional

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import RAGService
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_documents_to_vector_db(directory_path: str, verbose: bool = True) -> bool:
    """
    Load documents from a directory into the vector database.
    
    Args:
        directory_path: Path to the directory containing documents
        verbose: Whether to print detailed progress information
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate directory path
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return False
            
        if not directory.is_dir():
            logger.error(f"Path is not a directory: {directory_path}")
            return False
        
        # Check for supported files
        supported_extensions = ['.txt', '.pdf', '.md']
        supported_files = []
        for ext in supported_extensions:
            supported_files.extend(list(directory.glob(f"*{ext}")))
            supported_files.extend(list(directory.glob(f"**/*{ext}")))  # Recursive
        
        if not supported_files:
            logger.warning(f"No supported files found in {directory_path}")
            logger.info(f"Supported file types: {', '.join(supported_extensions)}")
            return False
        
        if verbose:
            print(f"\n📁 Loading documents from: {directory_path}")
            print(f"📄 Found {len(supported_files)} supported files:")
            for file in supported_files[:10]:  # Show first 10 files
                print(f"   - {file.name}")
            if len(supported_files) > 10:
                print(f"   ... and {len(supported_files) - 10} more files")
        
        # Initialize RAG service
        logger.info("Initializing RAG service...")
        rag_service = RAGService()
        
        # Get initial stats
        initial_stats = rag_service.get_collection_stats()
        initial_count = initial_stats.get('total_documents', 0)
        
        if verbose:
            print(f"\n🔢 Current documents in vector DB: {initial_count}")
            print(f"🧠 Using embedding model: {initial_stats.get('embedding_model', 'Unknown')}")
            print(f"📏 Chunk size: {initial_stats.get('chunk_size', 'Unknown')}")
            print(f"🔄 Chunk overlap: {initial_stats.get('chunk_overlap', 'Unknown')}")
        
        # Load documents
        logger.info(f"Loading documents from {directory_path}...")
        rag_service.add_documents_from_directory(str(directory_path))
        
        # Get final stats
        final_stats = rag_service.get_collection_stats()
        final_count = final_stats.get('total_documents', 0)
        added_count = final_count - initial_count
        
        if verbose:
            print(f"\n✅ Document loading completed!")
            print(f"📊 Documents added: {added_count}")
            print(f"📊 Total documents in vector DB: {final_count}")
            print(f"💾 Vector DB path: {settings.VECTOR_DB_PATH}")
        
        logger.info(f"Successfully loaded {added_count} document chunks")
        return True
        
    except Exception as e:
        logger.error(f"Error loading documents: {str(e)}")
        if verbose:
            print(f"\n❌ Error loading documents: {str(e)}")
        return False


def main():
    """Main function to handle command line arguments and run the document loader."""
    parser = argparse.ArgumentParser(
        description="Load documents into the Stevens AI Assistant vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load documents from the default documents directory
  python utils/load_documents.py
  
  # Load documents from a specific directory
  python utils/load_documents.py documents/stevens_policies
  
  # Load documents with minimal output
  python utils/load_documents.py documents/course_materials --quiet
  
Supported file formats:
  - PDF files (.pdf)
  - Text files (.txt)
  - Markdown files (.md)
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='documents',
        help='Directory containing documents to load (default: documents)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress verbose output'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only show current vector database statistics'
    )
    
    args = parser.parse_args()
    
    # Handle stats-only mode
    if args.stats_only:
        try:
            rag_service = RAGService()
            stats = rag_service.get_collection_stats()
            print(f"\n📊 Vector Database Statistics:")
            print(f"   Documents: {stats.get('total_documents', 0)}")
            print(f"   Embedding model: {stats.get('embedding_model', 'Unknown')}")
            print(f"   Chunk size: {stats.get('chunk_size', 'Unknown')}")
            print(f"   Chunk overlap: {stats.get('chunk_overlap', 'Unknown')}")
            print(f"   Storage path: {settings.VECTOR_DB_PATH}")
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            sys.exit(1)
        return
    
    # Validate RAG configuration
    if not settings.RAG_ENABLED:
        print("❌ RAG is disabled in configuration. Please enable it to load documents.")
        sys.exit(1)
    
    if not settings.OPENAI_API_KEY:
        print("❌ OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        sys.exit(1)
    
    # Load documents
    success = load_documents_to_vector_db(
        directory_path=args.directory,
        verbose=not args.quiet
    )
    
    if not success:
        sys.exit(1)
    
    if not args.quiet:
        print(f"\n🎉 All done! Your Stevens AI Assistant is now loaded with knowledge from {args.directory}")
        print("💡 Test it by asking questions about the loaded content!")


if __name__ == "__main__":
    main() 