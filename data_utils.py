import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_dataframe(rel_path: str):
    """
    Centralized helper to dynamically resolve the path and load a CSV file safely.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, rel_path)
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Successfully loaded CSV from {csv_path}")
        return df
    except FileNotFoundError:
        logger.error(f"CSV file not found at: {csv_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading CSV from {csv_path}: {e}")
        return None
