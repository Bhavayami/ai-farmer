class FarmerAssistantException(Exception):
    """Base class for all exceptions in the AI Farmer Assistant application."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class AgentException(FarmerAssistantException):
    """Raised when an individual AI Agent encounters an error."""
    pass

class OrchestrationException(FarmerAssistantException):
    """Raised when the central orchestrator fails to plan or route tasks."""
    pass

class DatabaseException(FarmerAssistantException):
    """Raised during database read/write or connection operations."""
    pass

class MCPException(FarmerAssistantException):
    """Raised when an external Model Context Protocol server/tool fails."""
    pass

class ValidationException(FarmerAssistantException):
    """Raised when inputs, parameters, or schemas fail validation check."""
    pass

class SecurityException(FarmerAssistantException):
    """Raised on unauthorized actions, prompt injection detections, or security violations."""
    pass
