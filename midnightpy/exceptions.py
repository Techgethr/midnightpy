"""
Custom exceptions for MidnightPy SDK.
"""

class BlockchainSDKException(Exception):
    """Base exception for all MidnightPy SDK errors."""
    pass

class GraphQLError(BlockchainSDKException):
    """Raised when a GraphQL query fails."""
    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []

class ConnectionError(BlockchainSDKException):
    """Raised when connection to the GraphQL endpoint fails."""
    pass

class ValidationError(BlockchainSDKException):
    """Raised when input validation fails."""
    pass

class SubscriptionError(BlockchainSDKException):
    """Raised when there's an error with WebSocket subscriptions."""
    pass

class AuthenticationError(BlockchainSDKException):
    """Raised when authentication fails."""
    pass 