"""
Base DXF Importer Interface

Defines the interface that all DXF importers must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional

class BaseDXFImporter(ABC):
    """Abstract base class for DXF importers."""
    
    def __init__(self, filepath: str, options: Optional[Dict[str, Any]] = None):
        """Initialize the importer with the given file and options.
        
        Args:
            filepath: Path to the DXF file to import
            options: Dictionary of import options
        """
        self.filepath = filepath
        self.options = options or {}
        self.errors = []
    
    @abstractmethod
    def read(self) -> bool:
        """Read and parse the DXF file.
        
        Returns:
            bool: True if the file was read successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_entities(self) -> Iterator[Any]:
        """Get an iterator over all entities in the DXF file.
        
        Yields:
            Entity objects from the DXF file
        """
        pass
    
    @abstractmethod
    def get_blocks(self) -> Dict[str, Any]:
        """Get all block definitions from the DXF file.
        
        Returns:
            Dictionary mapping block names to block definitions
        """
        pass
    
    @abstractmethod
    def import_to_scene(self, scene, collection, options: Optional[Dict[str, Any]] = None) -> list:
        """Import the DXF file into the given Blender scene and collection.
        
        Args:
            scene: The Blender scene to import into
            collection: The Blender collection to add objects to
            options: Additional import options
            
        Returns:
            List of error messages, if any
        """
        pass
    
    def add_error(self, message: str) -> None:
        """Add an error message to the importer's error list.
        
        Args:
            message: The error message to add
        """
        self.errors.append(message)
        print(f"[ERROR] {message}")
    
    def get_errors(self) -> list:
        """Get all error messages that occurred during import.
        
        Returns:
            List of error messages
        """
        return self.errors
