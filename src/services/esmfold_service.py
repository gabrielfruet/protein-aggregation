import requests
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

ESMFOLD_API_URL = "http://esmfold-service:5001/predict" 

def get_pdbs_from_sequences(sequences: List[str]) -> List[Optional[str]]:
    """
    Calls the ESMFold service to get PDBs for a list of sequences,
    one sequence at a time.
    """
    pdbs = []
    logger.info(f"Fetching PDBs for {len(sequences)} sequences from ESMFold service.")

    for sequence in sequences:
        payload = {"sequence": sequence}
        pdb_content = None

        try:
            response = requests.post(ESMFOLD_API_URL, json=payload, timeout=600)
            
            response.raise_for_status()
            
            pdb_content = response.json().get("pdb")
            logger.debug(f"Successfully processed sequence: {sequence[:15]}...")

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error for sequence {sequence[:15]}...: {http_err}")
            logger.error(f"Response body: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for sequence {sequence[:15]}...: {e}")
        
        pdbs.append(pdb_content)

    return pdbs