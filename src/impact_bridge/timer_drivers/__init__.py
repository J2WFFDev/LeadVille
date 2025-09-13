"""Timer drivers package for pluggable timer architecture."""

from .base import TimerDriverInterface, TimerDriverRegistry

# Create global registry instance  
registry = TimerDriverRegistry()

# Import and register drivers after creating registry
def _initialize_drivers():
    """Initialize and register timer drivers."""
    try:
        from .amg_driver import AMGTimerDriver
        registry.register_driver("amg_labs", AMGTimerDriver)
    except ImportError as e:
        print(f"Warning: Could not load AMG driver: {e}")
    
    try:
        from .specialpie_driver import SpecialPieTimerDriver
        registry.register_driver("specialpie", SpecialPieTimerDriver)
    except ImportError as e:
        print(f"Warning: Could not load SpecialPie driver: {e}")

# Initialize drivers on module load
_initialize_drivers()

__all__ = [
    "TimerDriverInterface", 
    "TimerDriverRegistry",
    "registry"
]