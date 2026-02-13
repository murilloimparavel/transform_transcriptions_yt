"""
Cliente para comunicação com a API.
"""
import requests
import streamlit as st
from typing import Optional, Dict, List
import json


class APIClient:
    """Cliente para comunicação com a API FastAPI."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def _get(self, endpoint: str) -> Optional[Dict]:
        """Faz requisição GET."""
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Erro na API: {str(e)}")
            return None
    
    def _post(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Faz requisição POST."""
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Erro na API: {str(e)}")
            return None
    
    def _delete(self, endpoint: str) -> bool:
        """Faz requisição DELETE."""
        try:
            response = requests.delete(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return True
        except Exception as e:
            st.error(f"Erro na API: {str(e)}")
            return False
    
    # Jobs
    def create_job(self, job_data: Dict) -> Optional[Dict]:
        """Cria um novo job."""
        return self._post("/api/jobs", job_data)
    
    def get_jobs(self, status_filter: Optional[str] = None) -> List[Dict]:
        """Lista jobs."""
        endpoint = "/api/jobs"
        if status_filter:
            endpoint += f"?status_filter={status_filter}"
        result = self._get(endpoint)
        return result if result else []
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Obtém detalhes de um job."""
        return self._get(f"/api/jobs/{job_id}")
    
    def get_job_progress(self, job_id: str) -> Optional[Dict]:
        """Obtém progresso de um job."""
        return self._get(f"/api/jobs/{job_id}/progress")
    
    def delete_job(self, job_id: str) -> bool:
        """Deleta um job."""
        return self._delete(f"/api/jobs/{job_id}")
    
    # Processing
    def start_processing(self, job_id: str) -> Optional[Dict]:
        """Inicia processamento de um job."""
        return self._post(f"/api/processing/start/{job_id}", {})
    
    def cancel_processing(self, job_id: str) -> Optional[Dict]:
        """Cancela processamento de um job."""
        return self._post(f"/api/processing/cancel/{job_id}", {})
    
    # Videos
    def get_videos(self, job_id: Optional[str] = None) -> List[Dict]:
        """Lista vídeos."""
        endpoint = "/api/videos"
        if job_id:
            endpoint += f"?job_id={job_id}"
        result = self._get(endpoint)
        return result if result else []
    
    # Results
    def get_results(
        self,
        job_id: Optional[str] = None,
        result_type: Optional[str] = None
    ) -> List[Dict]:
        """Lista resultados."""
        params = []
        if job_id:
            params.append(f"job_id={job_id}")
        if result_type:
            params.append(f"result_type={result_type}")
        
        endpoint = "/api/results"
        if params:
            endpoint += "?" + "&".join(params)
        
        result = self._get(endpoint)
        return result if result else []
    
    def get_result(self, result_id: str) -> Optional[Dict]:
        """Obtém detalhes de um resultado."""
        return self._get(f"/api/results/{result_id}")
    
    def health_check(self) -> bool:
        """Verifica se a API está online."""
        result = self._get("/health")
        return result is not None and result.get("status") == "healthy"

