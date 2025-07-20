"""Main entry point for the Raspibot application."""

import sys
from raspibot.utils.logging_config import setup_logging, set_correlation_id
from raspibot.utils.helpers import generate_correlation_id


def main():
    """Main application entry point."""
    # Setup logging
    logger = setup_logging()
    
    # Set correlation ID for this session
    session_id = generate_correlation_id()
    set_correlation_id(session_id, "main")
    
    logger.info("Raspibot starting up")
    logger.info("Foundation infrastructure ready")
    logger.info("Hardware interfaces available for implementation")
    logger.info("Configuration and logging systems operational")
    
    print("Raspibot Foundation Complete!")
    print("✅ Configuration Management")
    print("✅ Exception Handling") 
    print("✅ Hardware Interfaces")
    print("✅ Logging Infrastructure")
    print("✅ Utility Functions")
    print("✅ Testing Framework")
    print("\nReady for Iteration 2: Hardware Implementation!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 