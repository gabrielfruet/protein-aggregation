import asyncio
import aiohttp
from typing import List, Optional

ESMFOLD_API_URL = "http://esmfold-service:5001/predict"

async def get_pdb_async(session: aiohttp.ClientSession, sequence: str) -> Optional[str]:
    """Asynchronously gets a PDB for a single sequence."""
    try:
        async with session.post(ESMFOLD_API_URL, json={"sequence": sequence}) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("pdb")
    except Exception as e:
        print(f"Error fetching PDB for sequence {sequence[:10]}...: {e}")
        return None

async def get_pdbs_from_sequences_async(sequences: List[str]) -> List[Optional[str]]:
    """Runs all PDB requests concurrently."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
        tasks = [get_pdb_async(session, seq) for seq in sequences]
        pdb_results = await asyncio.gather(*tasks)
        return pdb_results