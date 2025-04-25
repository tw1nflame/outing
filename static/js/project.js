const autoCompleteButton = document.getElementById('autoComplete');
const docText = document.getElementById('doc-text');
const toggleChatButton = document.getElementById('toggleChat');
const chatSidebar = document.getElementById('chatSidebar');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat');
let suggestion = '';
let chatHistory = [];
let isAutocompleteLoading = false;
let isChatLoading = false;

// Функция для установки плейсхолдера
function setupPlaceholder() {
    if (!docText.textContent.trim()) {
        docText.setAttribute('data-empty', 'true');
    } else {
        docText.setAttribute('data-empty', 'false');
    }
}

// Инициализация плейсхолдера
setupPlaceholder();

// Слушатель изменений в поле документации
docText.addEventListener('input', setupPlaceholder);

// Слушатель фокуса
docText.addEventListener('focus', () => {
    docText.setAttribute('data-empty', 'false');
});

// Слушатель потери фокуса
docText.addEventListener('blur', () => {
    if (!docText.textContent.trim()) {
        docText.setAttribute('data-empty', 'true');
    }
});

// Функция добавления сообщения в чат
function addMessage(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    if (type !== 'system-message') {
        chatHistory.push({ message, type });
    }
}

// Обработчик нажатия кнопки автодополнения
autoCompleteButton.addEventListener('click', async () => {
    if (isAutocompleteLoading) {
        alert('Предыдущий запрос автодополнения еще обрабатывается');
        return;
    }

    const text = docText.textContent;
    const projectId = autoCompleteButton.dataset.projectId;

    // Очищаем предыдущую подсказку
    clearSuggestion();

    try {
        isAutocompleteLoading = true;
        autoCompleteButton.disabled = true;
        autoCompleteButton.textContent = 'Загрузка...';

        const response = await fetch(`/api/project/${projectId}/autocomplete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
        });

        const data = await response.json();

        if (response.ok) {
            if (data.suggestion && data.suggestion !== suggestion) {
                await showSuggestionAtCursor(data.suggestion);
            }
        } else if (response.status === 429) {
            alert('Предыдущий запрос автодополнения еще обрабатывается');
        } else if (response.status === 400) {
            alert('Проект не проиндексирован. Сначала выполните индексацию.');
        } else {
            alert(`Ошибка: ${data.detail || 'Неизвестная ошибка'}`);
        }
    } catch (error) {
        console.error('Error fetching autocomplete suggestion:', error);
        clearSuggestion();
        alert('Ошибка при получении автодополнения');
    } finally {
        setTimeout(() => {
            isAutocompleteLoading = false;
            autoCompleteButton.disabled = false;
            autoCompleteButton.textContent = 'Автодополнение';
        }, 1000); // Добавляем задержку для гарантии завершения всех операций
    }
});

// Сделаем функцию showSuggestionAtCursor асинхронной
async function showSuggestionAtCursor(suggestionText) {
    clearSuggestion();

    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    
    // Создаем span для подсказки
    const suggestionElement = document.createElement('span');
    suggestionElement.className = 'suggestion-text';
    suggestionElement.textContent = suggestionText;
    
    // Вставляем подсказку после текущей позиции курсора
    range.insertNode(suggestionElement);
    
    suggestion = suggestionText;
    
    // Возвращаем фокус на редактор и устанавливаем курсор перед подсказкой
    docText.focus();
    range.setStartBefore(suggestionElement);
    range.setEndBefore(suggestionElement);
    selection.removeAllRanges();
    selection.addRange(range);
}

// Функция очистки подсказки
function clearSuggestion() {
    const existingSuggestion = docText.querySelector('.suggestion-text');
    if (existingSuggestion) {
        existingSuggestion.remove();
    }
    suggestion = '';
}

// Обработчик нажатий клавиш
docText.addEventListener('keydown', (e) => {
    if (e.key === 'Tab' && suggestion) {
        e.preventDefault();
        const suggestionElement = docText.querySelector('.suggestion-text');
        if (suggestionElement) {
            const textNode = document.createTextNode(suggestionElement.textContent);
            suggestionElement.parentNode.replaceChild(textNode, suggestionElement);
            
            // Устанавливаем курсор после вставленного текста
            const range = document.createRange();
            range.setStartAfter(textNode);
            range.setEndAfter(textNode);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
        }
        clearSuggestion();
    } else if (e.key !== 'Tab') {
        clearSuggestion();
    }
});

// Обработчик сохранения документа
const saveDocButton = document.getElementById('saveDoc');
const docTitleDisplay = document.getElementById('doc-title-display');

saveDocButton.addEventListener('click', async () => {
    const projectId = saveDocButton.dataset.projectId;
    const title = docTitleDisplay.textContent;
    const content = docText.textContent;

    try {
        const response = await fetch(`/api/project/${projectId}/document`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                content: content
            }),
        });

        if (response.ok) {
            // После успешного сохранения перенаправляем на страницу документов
            window.location.href = `/project/${projectId}/documents`;
        } else {
            alert('Ошибка при сохранении документа');
        }
    } catch (error) {
        console.error('Error saving document:', error);
        alert('Ошибка при сохранении документа');
    }
});