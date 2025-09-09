#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Session Persistence Manager
Sistema completo de persistência e gerenciamento de sessões
"""

import os
import json
import logging
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

class SessionPersistenceManager:
    """Gerenciador completo de persistência de sessões"""

    def __init__(self):
        """Inicializa o gerenciador de persistência"""
        self.sessions_path = "sessions_data"
        self.backup_path = "sessions_backup"
        self._ensure_directories()
        
        logger.info("💾 Session Persistence Manager inicializado")

    def _ensure_directories(self):
        """Garante que todos os diretórios necessários existem"""
        directories = [
            self.sessions_path,
            self.backup_path,
            f"{self.sessions_path}/active",
            f"{self.sessions_path}/completed",
            f"{self.sessions_path}/metadata"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Diretório garantido: {directory}")

    def save_session_state(self, session_id: str, step: int, data: Dict[str, Any], 
                          context: Dict[str, Any] = None) -> bool:
        """
        Salva o estado completo de uma sessão
        
        Args:
            session_id: ID único da sessão
            step: Etapa atual (1, 2, 3)
            data: Dados da etapa
            context: Contexto adicional
        
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            timestamp = datetime.now()
            
            # Estrutura completa da sessão
            session_data = {
                "session_id": session_id,
                "current_step": step,
                "last_updated": timestamp.isoformat(),
                "created_at": timestamp.isoformat(),
                "status": "active",
                "context": context or {},
                "steps_data": {},
                "metadata": {
                    "total_steps": 3,
                    "completed_steps": [],
                    "failed_steps": [],
                    "execution_times": {}
                }
            }
            
            # Carrega dados existentes se houver
            existing_data = self.load_session_state(session_id)
            if existing_data:
                session_data.update({
                    "created_at": existing_data.get("created_at", timestamp.isoformat()),
                    "steps_data": existing_data.get("steps_data", {}),
                    "metadata": existing_data.get("metadata", session_data["metadata"])
                })
            
            # Atualiza dados da etapa atual
            session_data["steps_data"][f"step_{step}"] = {
                "data": data,
                "timestamp": timestamp.isoformat(),
                "status": "completed"
            }
            
            # Atualiza metadados
            if step not in session_data["metadata"]["completed_steps"]:
                session_data["metadata"]["completed_steps"].append(step)
            
            # Remove da lista de falhas se estava lá
            if step in session_data["metadata"]["failed_steps"]:
                session_data["metadata"]["failed_steps"].remove(step)
            
            # Salva arquivo principal
            session_file = f"{self.sessions_path}/active/{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Salva backup
            backup_file = f"{self.backup_path}/{session_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Salva metadados resumidos
            self._save_session_metadata(session_id, session_data)
            
            logger.info(f"💾 Sessão {session_id} salva - Etapa {step} concluída")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar sessão {session_id}: {e}")
            return False

    def save_session_from_analyses_data(self, session_id: str) -> bool:
        """
        Cria uma sessão no sistema de persistência baseada nos dados do analyses_data
        
        Args:
            session_id: ID da sessão
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            analyses_path = f"analyses_data/{session_id}"
            if not os.path.exists(analyses_path):
                logger.warning(f"⚠️ Diretório analyses_data não encontrado para sessão {session_id}")
                return False
            
            # Verifica quais etapas foram concluídas
            completed_steps = []
            context = {}
            
            # Verifica etapa 1
            etapa1_files = glob.glob(f"{analyses_path}/etapa1_concluida_*.json")
            if etapa1_files:
                completed_steps.append(1)
                try:
                    with open(etapa1_files[0], 'r', encoding='utf-8') as f:
                        etapa1_data = json.load(f)
                        if 'data' in etapa1_data and 'context' in etapa1_data['data']:
                            context = etapa1_data['data']['context']
                except:
                    pass
            
            # Verifica etapa 2
            etapa2_files = glob.glob(f"{analyses_path}/etapa2_concluida_*.json")
            if etapa2_files:
                completed_steps.append(2)
            
            # Verifica etapa 3
            etapa3_files = glob.glob(f"{analyses_path}/etapa3_concluida_*.json")
            if etapa3_files:
                completed_steps.append(3)
            
            if not completed_steps:
                logger.warning(f"⚠️ Nenhuma etapa concluída encontrada para sessão {session_id}")
                return False
            
            # Cria dados da sessão
            timestamp = datetime.now()
            session_data = {
                "session_id": session_id,
                "current_step": max(completed_steps),
                "last_updated": timestamp.isoformat(),
                "created_at": timestamp.isoformat(),
                "status": "completed" if 3 in completed_steps else "active",
                "context": context,
                "steps_data": {},
                "metadata": {
                    "total_steps": 3,
                    "completed_steps": completed_steps,
                    "failed_steps": [],
                    "execution_times": {}
                }
            }
            
            # Salva no local apropriado
            if session_data["status"] == "completed":
                session_file = f"{self.sessions_path}/completed/{session_id}.json"
            else:
                session_file = f"{self.sessions_path}/active/{session_id}.json"
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Salva metadados resumidos
            self._save_session_metadata(session_id, session_data)
            
            logger.info(f"💾 Sessão {session_id} importada do analyses_data - {len(completed_steps)} etapas concluídas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao importar sessão {session_id} do analyses_data: {e}")
            return False

    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Carrega o estado completo de uma sessão
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Dict com dados da sessão ou None se não encontrar
        """
        try:
            # Tenta carregar da pasta active primeiro
            session_file = f"{self.sessions_path}/active/{session_id}.json"
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"📂 Sessão {session_id} carregada (ativa)")
                    return data
            
            # Tenta carregar da pasta completed
            session_file = f"{self.sessions_path}/completed/{session_id}.json"
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"📂 Sessão {session_id} carregada (concluída)")
                    return data
            
            logger.warning(f"⚠️ Sessão {session_id} não encontrada")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar sessão {session_id}: {e}")
            return None

    def list_saved_sessions(self) -> List[Dict[str, Any]]:
        """
        Lista todas as sessões salvas com metadados
        
        Returns:
            Lista de dicionários com informações das sessões
        """
        sessions = []
        
        try:
            # Primeiro, importa sessões do analyses_data que ainda não estão no sistema
            self._import_sessions_from_analyses_data()
            
            # Sessões ativas
            active_path = f"{self.sessions_path}/active"
            if os.path.exists(active_path):
                for file_name in os.listdir(active_path):
                    if file_name.endswith('.json'):
                        session_id = file_name.replace('.json', '')
                        metadata = self._load_session_metadata(session_id)
                        if metadata:
                            metadata['status'] = 'active'
                            sessions.append(metadata)
            
            # Sessões concluídas
            completed_path = f"{self.sessions_path}/completed"
            if os.path.exists(completed_path):
                for file_name in os.listdir(completed_path):
                    if file_name.endswith('.json'):
                        session_id = file_name.replace('.json', '')
                        metadata = self._load_session_metadata(session_id)
                        if metadata:
                            metadata['status'] = 'completed'
                            sessions.append(metadata)
            
            # Ordena por data de criação (mais recente primeiro)
            sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logger.info(f"📋 {len(sessions)} sessões encontradas")
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar sessões: {e}")
            return []

    def _import_sessions_from_analyses_data(self):
        """
        Importa sessões do diretório analyses_data que ainda não estão no sistema
        """
        try:
            analyses_base = "analyses_data"
            if not os.path.exists(analyses_base):
                return
            
            for session_dir in os.listdir(analyses_base):
                if session_dir.startswith('session_'):
                    session_id = session_dir
                    
                    # Verifica se já existe no sistema
                    if (not os.path.exists(f"{self.sessions_path}/active/{session_id}.json") and 
                        not os.path.exists(f"{self.sessions_path}/completed/{session_id}.json")):
                        
                        # Importa a sessão
                        self.save_session_from_analyses_data(session_id)
                        
        except Exception as e:
            logger.error(f"❌ Erro ao importar sessões do analyses_data: {e}")

    def mark_session_completed(self, session_id: str) -> bool:
        """
        Marca uma sessão como concluída e move para pasta completed
        
        Args:
            session_id: ID da sessão
            
        Returns:
            bool: True se moveu com sucesso
        """
        try:
            active_file = f"{self.sessions_path}/active/{session_id}.json"
            completed_file = f"{self.sessions_path}/completed/{session_id}.json"
            
            if os.path.exists(active_file):
                # Carrega dados e atualiza status
                with open(active_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session_data['status'] = 'completed'
                session_data['completed_at'] = datetime.now().isoformat()
                
                # Salva na pasta completed
                with open(completed_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                
                # Remove da pasta active
                os.remove(active_file)
                
                # Atualiza metadados
                self._save_session_metadata(session_id, session_data)
                
                logger.info(f"✅ Sessão {session_id} marcada como concluída")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao marcar sessão como concluída: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Deleta uma sessão completamente
        
        Args:
            session_id: ID da sessão
            
        Returns:
            bool: True se deletou com sucesso
        """
        try:
            deleted = False
            
            # Remove da pasta active
            active_file = f"{self.sessions_path}/active/{session_id}.json"
            if os.path.exists(active_file):
                os.remove(active_file)
                deleted = True
            
            # Remove da pasta completed
            completed_file = f"{self.sessions_path}/completed/{session_id}.json"
            if os.path.exists(completed_file):
                os.remove(completed_file)
                deleted = True
            
            # Remove metadados
            metadata_file = f"{self.sessions_path}/metadata/{session_id}.json"
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
            
            if deleted:
                logger.info(f"🗑️ Sessão {session_id} deletada")
                return True
            else:
                logger.warning(f"⚠️ Sessão {session_id} não encontrada para deletar")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao deletar sessão: {e}")
            return False

    def get_session_step_data(self, session_id: str, step: int) -> Optional[Dict[str, Any]]:
        """
        Obtém dados de uma etapa específica
        
        Args:
            session_id: ID da sessão
            step: Número da etapa (1, 2, 3)
            
        Returns:
            Dict com dados da etapa ou None
        """
        session_data = self.load_session_state(session_id)
        if session_data:
            step_data = session_data.get('steps_data', {}).get(f'step_{step}')
            if step_data:
                return step_data.get('data')
        return None

    def can_continue_from_step(self, session_id: str, step: int) -> bool:
        """
        Verifica se é possível continuar de uma etapa específica
        
        Args:
            session_id: ID da sessão
            step: Etapa desejada
            
        Returns:
            bool: True se pode continuar
        """
        session_data = self.load_session_state(session_id)
        if not session_data:
            return False
        
        completed_steps = session_data.get('metadata', {}).get('completed_steps', [])
        
        # Para continuar da etapa N, precisa ter concluído a etapa N-1
        if step == 1:
            return True  # Sempre pode começar da etapa 1
        elif step == 2:
            return 1 in completed_steps
        elif step == 3:
            return 1 in completed_steps and 2 in completed_steps
        
        return False

    def _save_session_metadata(self, session_id: str, session_data: Dict[str, Any]):
        """Salva metadados resumidos da sessão"""
        try:
            metadata = {
                "session_id": session_id,
                "created_at": session_data.get("created_at"),
                "last_updated": session_data.get("last_updated"),
                "status": session_data.get("status"),
                "current_step": session_data.get("current_step"),
                "completed_steps": session_data.get("metadata", {}).get("completed_steps", []),
                "context": {
                    "segmento": session_data.get("context", {}).get("segmento", "N/A"),
                    "produto": session_data.get("context", {}).get("produto", "N/A"),
                    "publico": session_data.get("context", {}).get("publico", "N/A")
                }
            }
            
            metadata_file = f"{self.sessions_path}/metadata/{session_id}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar metadados: {e}")

    def _load_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carrega metadados de uma sessão"""
        try:
            metadata_file = f"{self.sessions_path}/metadata/{session_id}.json"
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao carregar metadados: {e}")
            return None

    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Remove sessões antigas
        
        Args:
            days_old: Dias para considerar sessão antiga
            
        Returns:
            int: Número de sessões removidas
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            removed_count = 0
            
            for status in ['active', 'completed']:
                path = f"{self.sessions_path}/{status}"
                if os.path.exists(path):
                    for file_name in os.listdir(path):
                        if file_name.endswith('.json'):
                            file_path = os.path.join(path, file_name)
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            
                            if file_time < cutoff_date:
                                session_id = file_name.replace('.json', '')
                                if self.delete_session(session_id):
                                    removed_count += 1
            
            logger.info(f"🧹 {removed_count} sessões antigas removidas")
            return removed_count
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")
            return 0

# Instância global
session_manager = SessionPersistenceManager()