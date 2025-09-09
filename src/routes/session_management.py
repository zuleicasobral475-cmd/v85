#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Session Management Routes
APIs para gerenciamento completo de sessões
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, Any
from services.session_persistence_manager import session_manager

logger = logging.getLogger(__name__)

# Blueprint para gerenciamento de sessões
session_bp = Blueprint('session_management', __name__)

@session_bp.route('/sessions/list', methods=['GET'])
def list_sessions():
    """
    Lista todas as sessões salvas
    
    Returns:
        JSON com lista de sessões e metadados
    """
    try:
        sessions = session_manager.list_saved_sessions()
        
        # Formatar dados para o frontend
        formatted_sessions = []
        for session in sessions:
            formatted_session = {
                'session_id': session.get('session_id'),
                'created_at': session.get('created_at'),
                'last_updated': session.get('last_updated'),
                'status': session.get('status'),
                'current_step': session.get('current_step'),
                'completed_steps': session.get('completed_steps', []),
                'context': session.get('context', {}),
                'display_name': f"Sessão {session.get('session_id', 'N/A')[:8]}... - {session.get('context', {}).get('segmento', 'N/A')}",
                'can_continue': {
                    'step_1': True,
                    'step_2': 1 in session.get('completed_steps', []),
                    'step_3': 1 in session.get('completed_steps', []) and 2 in session.get('completed_steps', [])
                }
            }
            formatted_sessions.append(formatted_session)
        
        return jsonify({
            'success': True,
            'sessions': formatted_sessions,
            'total': len(formatted_sessions)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar sessões: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@session_bp.route('/sessions/load/<session_id>', methods=['GET'])
def load_session(session_id: str):
    """
    Carrega uma sessão específica
    
    Args:
        session_id: ID da sessão
        
    Returns:
        JSON com dados completos da sessão
    """
    try:
        session_data = session_manager.load_session_state(session_id)
        
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Sessão não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'session_data': session_data
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar sessão {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@session_bp.route('/sessions/load-step/<session_id>/<int:step>', methods=['GET'])
def load_session_step(session_id: str, step: int):
    """
    Carrega dados de uma etapa específica
    
    Args:
        session_id: ID da sessão
        step: Número da etapa (1, 2, 3)
        
    Returns:
        JSON com dados da etapa
    """
    try:
        if step not in [1, 2, 3]:
            return jsonify({
                'success': False,
                'error': 'Etapa deve ser 1, 2 ou 3'
            }), 400
        
        step_data = session_manager.get_session_step_data(session_id, step)
        
        if not step_data:
            return jsonify({
                'success': False,
                'error': f'Dados da etapa {step} não encontrados'
            }), 404
        
        return jsonify({
            'success': True,
            'step': step,
            'data': step_data
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar etapa {step} da sessão {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@session_bp.route('/sessions/can-continue/<session_id>/<int:step>', methods=['GET'])
def can_continue_from_step(session_id: str, step: int):
    """
    Verifica se é possível continuar de uma etapa específica
    
    Args:
        session_id: ID da sessão
        step: Etapa desejada
        
    Returns:
        JSON indicando se pode continuar
    """
    try:
        if step not in [1, 2, 3]:
            return jsonify({
                'success': False,
                'error': 'Etapa deve ser 1, 2 ou 3'
            }), 400
        
        can_continue = session_manager.can_continue_from_step(session_id, step)
        
        return jsonify({
            'success': True,
            'can_continue': can_continue,
            'step': step
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar continuidade: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@session_bp.route('/sessions/continue/<session_id>/<int:step>', methods=['POST'])
def continue_from_step(session_id: str, step: int):
    """
    Continua execução de uma etapa específica
    
    Args:
        session_id: ID da sessão
        step: Etapa para continuar
        
    Returns:
        JSON com resultado da operação
    """
    try:
        if step not in [1, 2, 3]:
            return jsonify({
                'success': False,
                'error': 'Etapa deve ser 1, 2 ou 3'
            }), 400
        
        # Verifica se pode continuar
        if not session_manager.can_continue_from_step(session_id, step):
            return jsonify({
                'success': False,
                'error': f'Não é possível continuar da etapa {step}. Verifique se as etapas anteriores foram concluídas.'
            }), 400
        
        # Carrega dados da sessão
        session_data = session_manager.load_session_state(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Sessão não encontrada'
            }), 404
        
        # Prepara dados para continuar
        context = session_data.get('context', {})
        context['session_id'] = session_id
        
        # Dados das etapas anteriores
        previous_data = {}
        for i in range(1, step):
            step_data = session_manager.get_session_step_data(session_id, i)
            if step_data:
                previous_data[f'step_{i}'] = step_data
        
        return jsonify({
            'success': True,
            'message': f'Pronto para continuar da etapa {step}',
            'session_id': session_id,
            'step': step,
            'context': context,
            'previous_data': previous_data
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao continuar da etapa {step}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@session_bp.route('/sessions/delete/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """
    Deleta uma sessão
    
    Args:
        session_id: ID da sessão
        
    Returns:
        JSON com resultado da operação
    """
    try:
        success = session_manager.delete_session(session_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Sessão {session_id} deletada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sessão não encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Erro ao deletar sessão {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@session_bp.route('/sessions/mark-completed/<session_id>', methods=['POST'])
def mark_session_completed(session_id: str):
    """
    Marca uma sessão como concluída
    
    Args:
        session_id: ID da sessão
        
    Returns:
        JSON com resultado da operação
    """
    try:
        success = session_manager.mark_session_completed(session_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Sessão {session_id} marcada como concluída'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sessão não encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Erro ao marcar sessão como concluída: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@session_bp.route('/sessions/cleanup', methods=['POST'])
def cleanup_old_sessions():
    """
    Remove sessões antigas
    
    Returns:
        JSON com número de sessões removidas
    """
    try:
        data = request.get_json() or {}
        days_old = data.get('days_old', 30)
        
        removed_count = session_manager.cleanup_old_sessions(days_old)
        
        return jsonify({
            'success': True,
            'removed_count': removed_count,
            'message': f'{removed_count} sessões antigas removidas'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na limpeza de sessões: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@session_bp.route('/sessions/save-state', methods=['POST'])
def save_session_state():
    """
    Salva estado de uma sessão
    
    Returns:
        JSON com resultado da operação
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        session_id = data.get('session_id')
        step = data.get('step')
        step_data = data.get('data')
        context = data.get('context')
        
        if not all([session_id, step, step_data]):
            return jsonify({
                'success': False,
                'error': 'session_id, step e data são obrigatórios'
            }), 400
        
        success = session_manager.save_session_state(session_id, step, step_data, context)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Estado da sessão {session_id} salvo para etapa {step}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao salvar estado da sessão'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Erro ao salvar estado da sessão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500