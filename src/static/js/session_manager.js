// ARQV30 Enhanced v3.0 - Session Manager
console.log('🔧 Session Manager carregado');

// Variáveis globais para gerenciamento de sessões
let selectedSessionId = null;
let selectedStep = null;
let availableSessions = [];

// Carrega sessões salvas
async function loadSavedSessions() {
    try {
        const response = await fetch('/api/sessions/list');
        const result = await response.json();
        
        if (result.success) {
            availableSessions = result.sessions;
            displaySavedSessions(result.sessions);
        } else {
            console.error('Erro ao carregar sessões:', result.error);
            displaySavedSessions([]);
        }
    } catch (error) {
        console.error('Erro ao carregar sessões:', error);
        displaySavedSessions([]);
    }
}

// Exibe sessões salvas na interface
function displaySavedSessions(sessions) {
    const container = document.getElementById('savedSessionsList');
    
    if (!sessions || sessions.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-inbox"></i>
                <p>Nenhuma sessão salva encontrada</p>
            </div>
        `;
        return;
    }
    
    const sessionsHtml = sessions.map(session => {
        const createdDate = new Date(session.created_at).toLocaleString('pt-BR');
        const lastUpdated = new Date(session.last_updated).toLocaleString('pt-BR');
        const completedSteps = session.completed_steps || [];
        const statusClass = session.status === 'completed' ? 'success' : 'primary';
        const statusIcon = session.status === 'completed' ? 'check-circle' : 'clock';
        
        return `
            <div class="session-item" data-session-id="${session.session_id}">
                <div class="session-header">
                    <div class="session-title">
                        <i class="fas fa-folder"></i>
                        <span>${session.display_name || `Sessão ${session.session_id.substring(0, 8)}...`}</span>
                        <span class="badge bg-${statusClass}">
                            <i class="fas fa-${statusIcon}"></i>
                            ${session.status === 'completed' ? 'Concluída' : 'Ativa'}
                        </span>
                    </div>
                    <div class="session-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="selectSession('${session.session_id}')">
                            <i class="fas fa-hand-pointer"></i> Selecionar
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteSession('${session.session_id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="session-details">
                    <div class="session-info">
                        <small class="text-muted">
                            <i class="fas fa-calendar"></i> Criada: ${createdDate}<br>
                            <i class="fas fa-clock"></i> Atualizada: ${lastUpdated}
                        </small>
                    </div>
                    <div class="session-progress">
                        <div class="progress-steps">
                            ${[1, 2, 3].map(step => {
                                const isCompleted = completedSteps.includes(step);
                                const stepClass = isCompleted ? 'completed' : 'pending';
                                const stepIcon = isCompleted ? 'check' : 'circle';
                                return `
                                    <span class="step-indicator ${stepClass}">
                                        <i class="fas fa-${stepIcon}"></i>
                                        ${step}
                                    </span>
                                `;
                            }).join('')}
                        </div>
                    </div>
                    <div class="session-context">
                        <small>
                            <strong>Segmento:</strong> ${session.context?.segmento || 'N/A'}<br>
                            <strong>Produto:</strong> ${session.context?.produto || 'N/A'}
                        </small>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = sessionsHtml;
}

// Seleciona uma sessão
async function selectSession(sessionId) {
    try {
        selectedSessionId = sessionId;
        
        // Carrega dados da sessão
        const response = await fetch(`/api/sessions/load/${sessionId}`);
        const result = await response.json();
        
        if (result.success) {
            const sessionData = result.session_data;
            
            // Atualiza interface
            updateSelectedSessionInfo(sessionData);
            updateStepSelector(sessionData);
            
            // Marca sessão como selecionada visualmente
            document.querySelectorAll('.session-item').forEach(item => {
                item.classList.remove('selected');
            });
            document.querySelector(`[data-session-id="${sessionId}"]`).classList.add('selected');
            
            if (typeof window.showNotification === 'function') {
                window.showNotification(`Sessão selecionada: ${sessionId.substring(0, 8)}...`, 'success');
            } else {
                console.log(`Sessão selecionada: ${sessionId.substring(0, 8)}...`);
            }
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Erro ao selecionar sessão:', error);
        if (typeof window.showNotification === 'function') {
            window.showNotification(`Erro ao selecionar sessão: ${error.message}`, 'error');
        } else {
            console.error(`Erro ao selecionar sessão: ${error.message}`);
        }
    }
}

// Atualiza informações da sessão selecionada
function updateSelectedSessionInfo(sessionData) {
    const container = document.getElementById('selectedSessionInfo');
    
    if (!sessionData) {
        container.innerHTML = '<span class="text-muted">Nenhuma sessão selecionada</span>';
        return;
    }
    
    const createdDate = new Date(sessionData.created_at).toLocaleString('pt-BR');
    const completedSteps = sessionData.metadata?.completed_steps || [];
    
    container.innerHTML = `
        <div class="selected-session-details">
            <div class="session-id">
                <strong>ID:</strong> ${sessionData.session_id.substring(0, 12)}...
            </div>
            <div class="session-date">
                <strong>Criada:</strong> ${createdDate}
            </div>
            <div class="session-steps">
                <strong>Etapas concluídas:</strong> ${completedSteps.join(', ') || 'Nenhuma'}
            </div>
            <div class="session-context">
                <strong>Segmento:</strong> ${sessionData.context?.segmento || 'N/A'}
            </div>
        </div>
    `;
}

// Atualiza seletor de etapas
function updateStepSelector(sessionData) {
    const completedSteps = sessionData.metadata?.completed_steps || [];
    
    // Atualiza botões de etapa
    for (let step = 1; step <= 3; step++) {
        const btn = document.querySelector(`[data-step="${step}"]`);
        if (btn) {
            // Verifica se pode continuar desta etapa
            const canContinue = canContinueFromStep(step, completedSteps);
            btn.disabled = !canContinue;
            
            if (completedSteps.includes(step)) {
                btn.classList.add('completed');
                btn.innerHTML = `<i class="fas fa-check"></i> Etapa ${step} (Concluída)`;
            } else if (canContinue) {
                btn.classList.remove('completed');
                btn.innerHTML = `<i class="fas fa-play"></i> Etapa ${step}`;
            } else {
                btn.classList.remove('completed');
                btn.innerHTML = `<i class="fas fa-lock"></i> Etapa ${step} (Bloqueada)`;
            }
        }
    }
}

// Verifica se pode continuar de uma etapa
function canContinueFromStep(step, completedSteps) {
    if (step === 1) return true; // Sempre pode começar da etapa 1
    if (step === 2) return completedSteps.includes(1);
    if (step === 3) return completedSteps.includes(1) && completedSteps.includes(2);
    return false;
}

// Seleciona uma etapa
function selectStep(step) {
    if (!selectedSessionId) {
        if (typeof window.showNotification === 'function') {
            window.showNotification('Selecione uma sessão primeiro', 'warning');
        } else {
            console.warn('Selecione uma sessão primeiro');
        }
        return;
    }
    
    const btn = document.querySelector(`[data-step="${step}"]`);
    if (btn && btn.disabled) {
        if (typeof window.showNotification === 'function') {
            window.showNotification(`Etapa ${step} não disponível. Complete as etapas anteriores primeiro.`, 'warning');
        } else {
            console.warn(`Etapa ${step} não disponível. Complete as etapas anteriores primeiro.`);
        }
        return;
    }
    
    selectedStep = step;
    
    // Atualiza interface
    document.querySelectorAll('.step-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    
    // Habilita botão de continuar
    document.getElementById('continueBtn').disabled = false;
    
    if (typeof window.showNotification === 'function') {
        window.showNotification(`Etapa ${step} selecionada`, 'info');
    } else {
        console.log(`Etapa ${step} selecionada`);
    }
}

// Continua execução de uma etapa
async function continueFromStep() {
    if (!selectedSessionId || !selectedStep) {
        if (typeof window.showNotification === 'function') {
            window.showNotification('Selecione uma sessão e etapa primeiro', 'warning');
        } else {
            console.warn('Selecione uma sessão e etapa primeiro');
        }
        return;
    }
    
    try {
        // Verifica se pode continuar
        const checkResponse = await fetch(`/api/sessions/can-continue/${selectedSessionId}/${selectedStep}`);
        const checkResult = await checkResponse.json();
        
        if (!checkResult.success || !checkResult.can_continue) {
            throw new Error('Não é possível continuar desta etapa');
        }
        
        // Define sessão atual
        currentSessionId = selectedSessionId;
        
        // Carrega dados da sessão no formulário se necessário
        await loadSessionDataToForm(selectedSessionId);
        
        // Inicia a etapa selecionada
        switch (selectedStep) {
            case 1:
                await startStep1();
                break;
            case 2:
                await startStep2();
                break;
            case 3:
                await startStep3();
                break;
        }
        
        if (typeof window.showNotification === 'function') {
            window.showNotification(`Continuando execução da etapa ${selectedStep}`, 'success');
        } else {
            console.log(`Continuando execução da etapa ${selectedStep}`);
        }
        
    } catch (error) {
        console.error('Erro ao continuar execução:', error);
        if (typeof window.showNotification === 'function') {
            window.showNotification(`Erro ao continuar: ${error.message}`, 'error');
        } else {
            console.error(`Erro ao continuar: ${error.message}`);
        }
    }
}

// Carrega dados da sessão no formulário
async function loadSessionDataToForm(sessionId) {
    try {
        const response = await fetch(`/api/sessions/load/${sessionId}`);
        const result = await response.json();
        
        if (result.success && result.session_data.context) {
            const context = result.session_data.context;
            
            // Preenche formulário com dados da sessão
            Object.entries(context).forEach(([key, value]) => {
                const element = document.getElementById(key);
                if (element && value) {
                    element.value = value;
                }
            });
        }
    } catch (error) {
        console.error('Erro ao carregar dados da sessão:', error);
    }
}

// Inicia nova sessão
function startNewSession() {
    selectedSessionId = null;
     currentSessionId = null;
    
    // Reset interface
    document.getElementById('selectedSessionInfo').innerHTML = '<span class="text-muted">Nenhuma sessão selecionada</span>';
    document.getElementById('continueBtn').disabled = true;
    
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    document.querySelectorAll('.step-btn').forEach(btn => {
        btn.classList.remove('selected');
        btn.disabled = true;
    });
    
    if (typeof window.showNotification === 'function') {
        window.showNotification('Nova sessão iniciada', 'info');
    } else {
        console.log('Nova sessão iniciada');
    }
}

// Deleta uma sessão
async function deleteSession(sessionId) {
    if (!confirm('Tem certeza que deseja deletar esta sessão? Esta ação não pode ser desfeita.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sessions/delete/${sessionId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (typeof window.showNotification === 'function') {
                window.showNotification('Sessão deletada com sucesso', 'success');
            } else {
                console.log('Sessão deletada com sucesso');
            }
            
            // Se era a sessão selecionada, limpa seleção
            if (selectedSessionId === sessionId) {
                startNewSession();
            }
            
            // Recarrega lista
            loadSavedSessions();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Erro ao deletar sessão:', error);
        if (typeof window.showNotification === 'function') {
            window.showNotification(`Erro ao deletar sessão: ${error.message}`, 'error');
        } else {
            console.error(`Erro ao deletar sessão: ${error.message}`);
        }
    }
}

// Salva estado da sessão
async function saveSessionState(sessionId, step, data, context = null) {
    try {
        const response = await fetch('/api/sessions/save-state', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                step: step,
                data: data,
                context: context
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`✅ Estado da sessão ${sessionId} salvo para etapa ${step}`);
            
            // Recarrega lista de sessões para atualizar status
            loadSavedSessions();
        } else {
            console.error('Erro ao salvar estado:', result.error);
        }
    } catch (error) {
        console.error('Erro ao salvar estado da sessão:', error);
    }
}

// Função utilitária para formatar tamanho de arquivo
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Exposição de funções globais
window.loadSavedSessions = loadSavedSessions;
window.selectSession = selectSession;
window.selectStep = selectStep;
window.continueFromStep = continueFromStep;
window.startNewSession = startNewSession;
window.deleteSession = deleteSession;
window.saveSessionState = saveSessionState;

// Inicialização automática
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Session Manager inicializado');
    
    // Carrega sessões automaticamente
    setTimeout(loadSavedSessions, 1000);
});

