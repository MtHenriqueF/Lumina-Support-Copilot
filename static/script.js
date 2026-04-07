const APP_CONFIG = window.APP_CONFIG || {};

let messages = [];
let isLoading = false;

const welcomeScreen = document.getElementById('welcomeScreen');
const messagesArea = document.getElementById('messagesArea');
const messagesContainer = document.getElementById('messagesContainer');
const loadingIndicator = document.getElementById('loadingIndicator');
const messagesEnd = document.getElementById('messagesEnd');
const clearBtn = document.getElementById('clearBtn');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const modelSelect = document.getElementById('modelSelect');
const sendButton = document.getElementById('sendButton');
const sendLabel = document.getElementById('sendLabel');
const loadingSpinner = document.getElementById('loadingSpinner');
const charCounter = document.getElementById('charCounter');
const statusPill = document.getElementById('statusPill');
const lastMeta = document.getElementById('lastMeta');
const emptyInsights = document.getElementById('emptyInsights');
const insightsContent = document.getElementById('insightsContent');
const summaryText = document.getElementById('summaryText');
const priorityBadge = document.getElementById('priorityBadge');
const categoryBadge = document.getElementById('categoryBadge');
const languageBadge = document.getElementById('languageBadge');
const resolutionBadge = document.getElementById('resolutionBadge');
const sentimentValue = document.getElementById('sentimentValue');
const sentimentBarFill = document.getElementById('sentimentBarFill');
const tagsList = document.getElementById('tagsList');
const actionText = document.getElementById('actionText');
const responseText = document.getElementById('responseText');
const modelHintNodes = document.querySelectorAll('[data-model-hint]');
const suggestionChips = document.querySelectorAll('.suggestion-chip');

document.addEventListener('DOMContentLoaded', () => {
    modelSelect.value = APP_CONFIG.defaultModel || modelSelect.value;
    setupEventListeners();
    autoResizeTextarea();
    updateComposerMeta();
    updateSendButton();
    updateModelHint();
});

function setupEventListeners() {
    chatForm.addEventListener('submit', handleSubmit);
    clearBtn.addEventListener('click', clearChat);
    modelSelect.addEventListener('change', updateModelHint);
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keydown', handleKeyDown);
    suggestionChips.forEach((chip) => chip.addEventListener('click', handleSuggestionClick));
}

function handleSuggestionClick(event) {
    const prompt = event.currentTarget.dataset.prompt || '';
    messageInput.value = prompt;
    autoResizeTextarea();
    updateComposerMeta();
    updateSendButton();
    messageInput.focus();
}

function handleSubmit(event) {
    event.preventDefault();

    const content = messageInput.value.trim();
    const model = modelSelect.value;
    if (!content || isLoading) {
        return;
    }

    sendMessage(content, model);
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSubmit(event);
    }
}

function handleInputChange() {
    autoResizeTextarea();
    updateComposerMeta();
    updateSendButton();
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = `${Math.min(messageInput.scrollHeight, 180)}px`;
}

function updateComposerMeta() {
    const currentLength = messageInput.value.length;
    charCounter.textContent = `${currentLength} / ${APP_CONFIG.messageMaxChars || messageInput.maxLength}`;
}

function updateModelHint() {
    modelHintNodes.forEach((node) => {
        node.hidden = node.dataset.modelHint !== modelSelect.value;
    });
}

function updateSendButton() {
    sendButton.disabled = isLoading || messageInput.value.trim().length === 0;
}

async function sendMessage(content, model) {
    const userMessage = {
        id: `${Date.now()}-user`,
        type: 'user',
        content,
        timestamp: new Date(),
    };

    messages.push(userMessage);
    displayMessage(userMessage);
    hideWelcomeScreen();
    showClearButton();

    messageInput.value = '';
    autoResizeTextarea();
    updateComposerMeta();
    setLoadingState(true);

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: content, model }),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(extractErrorMessage(data));
        }

        const aiMessage = {
            id: `${Date.now()}-assistant`,
            type: 'ai',
            content: data.response,
            payload: data,
            model: data.model || model,
            duration: data.duration,
            timestamp: new Date(),
        };

        messages.push(aiMessage);
        displayMessage(aiMessage);
        renderInsights(data);
    } catch (error) {
        const aiMessage = {
            id: `${Date.now()}-error`,
            type: 'ai',
            content: error.message || 'Nao foi possivel processar a solicitacao.',
            isError: true,
            model,
            timestamp: new Date(),
        };

        messages.push(aiMessage);
        displayMessage(aiMessage);
        statusPill.textContent = 'Falha na ultima solicitacao';
        statusPill.className = 'status-pill danger';
    } finally {
        setLoadingState(false);
    }
}

function displayMessage(message) {
    const messageElement = document.createElement('article');
    messageElement.className = `message-row ${message.type}`;

    const sender = message.type === 'user' ? 'Voce' : 'Lumina';
    const time = message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const modelChip = message.model ? `<span class="inline-chip">${escapeHtml(message.model)}</span>` : '';
    const durationChip = Number.isFinite(message.duration)
        ? `<span class="inline-chip">${formatDuration(message.duration)}</span>`
        : '';

    let detailBlock = '';
    if (message.type === 'ai' && message.payload) {
        detailBlock = `
            <div class="message-highlights">
                <span class="badge ${priorityBadgeClass(message.payload.priority)}">${escapeHtml(message.payload.priority)}</span>
                <span class="badge ${categoryBadgeClass(message.payload.category)}">${escapeHtml(message.payload.category)}</span>
                <span class="inline-note">${escapeHtml(message.payload.summary)}</span>
            </div>
        `;
    }

    if (message.type === 'ai' && message.isError) {
        detailBlock = '<div class="message-error-note">A resposta abaixo veio do tratamento de erro da aplicacao.</div>';
    }

    messageElement.innerHTML = `
        <div class="message-avatar ${message.type}">
            ${message.type === 'user' ? 'U' : 'AI'}
        </div>
        <div class="message-card ${message.type}${message.isError ? ' error' : ''}">
            <div class="message-meta">
                <div class="message-title">
                    <strong>${sender}</strong>
                    ${modelChip}
                    ${durationChip}
                </div>
                <span>${time}</span>
            </div>
            <p class="message-text">${escapeHtml(message.content)}</p>
            ${detailBlock}
        </div>
    `;

    messagesContainer.appendChild(messageElement);
    scrollToBottom();
}

function renderInsights(data) {
    emptyInsights.hidden = true;
    insightsContent.hidden = false;

    summaryText.textContent = data.summary || 'Sem resumo disponivel.';
    priorityBadge.className = `badge ${priorityBadgeClass(data.priority)}`;
    priorityBadge.textContent = data.priority || 'Medium';

    categoryBadge.className = `badge ${categoryBadgeClass(data.category)}`;
    categoryBadge.textContent = data.category || 'general';

    languageBadge.textContent = data.language || 'n/a';
    resolutionBadge.textContent = data.is_resolved ? 'Resolvido' : 'Em aberto';

    const sentiment = clampNumber(data.sentiment, 0, 100, 50);
    sentimentValue.textContent = sentiment;
    sentimentBarFill.style.width = `${sentiment}%`;
    sentimentBarFill.className = `sentiment-fill ${sentimentToneClass(sentiment)}`;

    tagsList.innerHTML = '';
    (Array.isArray(data.tags) ? data.tags : []).forEach((tag) => {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.textContent = tag;
        tagsList.appendChild(chip);
    });
    if (!tagsList.children.length) {
        const fallbackTag = document.createElement('span');
        fallbackTag.className = 'tag-chip';
        fallbackTag.textContent = 'support';
        tagsList.appendChild(fallbackTag);
    }

    actionText.textContent = data.action || 'Sem acao recomendada.';
    responseText.textContent = data.response || 'Sem resposta sugerida.';

    lastMeta.textContent = `${data.model || modelSelect.value} · ${formatDuration(data.duration)}`;
    statusPill.textContent = 'Analise concluida';
    statusPill.className = 'status-pill success';
}

function setLoadingState(loading) {
    isLoading = loading;
    messageInput.disabled = loading;
    modelSelect.disabled = loading;
    updateSendButton();

    loadingIndicator.hidden = !loading;
    loadingSpinner.hidden = !loading;
    sendLabel.textContent = loading ? 'Analisando...' : 'Analisar ticket';
    statusPill.textContent = loading ? 'Gerando analise estruturada' : statusPill.textContent;
    statusPill.className = loading ? 'status-pill loading' : statusPill.className;

    if (loading) {
        scrollToBottom();
    }
}

function clearChat() {
    messages = [];
    messagesContainer.innerHTML = '';
    setLoadingState(false);
    clearBtn.hidden = true;
    welcomeScreen.hidden = false;
    emptyInsights.hidden = false;
    insightsContent.hidden = true;
    statusPill.textContent = 'Pronto para analisar';
    statusPill.className = 'status-pill';
    lastMeta.textContent = 'Sem respostas ainda';
    summaryText.textContent = '';
    actionText.textContent = '';
    responseText.textContent = '';
    tagsList.innerHTML = '';
    messageInput.disabled = false;
    modelSelect.disabled = false;
    messageInput.focus();
    updateSendButton();
}

function hideWelcomeScreen() {
    welcomeScreen.hidden = true;
}

function showClearButton() {
    clearBtn.hidden = false;
}

function scrollToBottom() {
    messagesEnd.scrollIntoView({ behavior: 'smooth', block: 'end' });
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function extractErrorMessage(data) {
    if (data && data.error && typeof data.error === 'object' && data.error.message) {
        return data.error.message;
    }
    if (data && typeof data.error === 'string') {
        return data.error;
    }
    return 'Nao foi possivel concluir a solicitacao.';
}

function priorityBadgeClass(priority) {
    switch ((priority || '').toLowerCase()) {
        case 'critical':
            return 'priority-critical';
        case 'high':
            return 'priority-high';
        case 'low':
            return 'priority-low';
        default:
            return 'priority-medium';
    }
}

function categoryBadgeClass(category) {
    switch ((category || '').toLowerCase()) {
        case 'technical':
            return 'category-technical';
        case 'billing':
            return 'category-billing';
        default:
            return 'category-general';
    }
}

function sentimentToneClass(sentiment) {
    if (sentiment >= 70) {
        return 'tone-positive';
    }
    if (sentiment <= 39) {
        return 'tone-negative';
    }
    return 'tone-neutral';
}

function clampNumber(value, min, max, fallback) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return fallback;
    }
    return Math.min(max, Math.max(min, parsed));
}

function formatDuration(value) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return '--';
    }
    return `${parsed.toFixed(2)}s`;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}
