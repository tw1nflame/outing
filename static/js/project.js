tinymce.init({
    selector: '#doc-text',
    plugins: 'lists',
    toolbar: 'bold italic | bullist numlist | indent outdent'
});

const titleDisplay = document.getElementById('doc-title-display');
const titleInput = document.getElementById('doc-title');

titleDisplay.addEventListener('dblclick', () => {
    titleInput.value = titleDisplay.textContent;
    titleDisplay.style.display = 'none';
    titleInput.style.display = 'block';
    titleInput.focus();
});

titleInput.addEventListener('blur', () => {
    titleDisplay.textContent = titleInput.value || 'Новый документ 1';
    titleDisplay.style.display = 'block';
    titleInput.style.display = 'none';
});

titleInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        titleInput.blur();
    }
});

titleDisplay.addEventListener('mouseenter', () => {
    titleDisplay.style.outline = '1px dashed #888';
    titleDisplay.style.cursor = 'pointer';
});
titleDisplay.addEventListener('mouseleave', () => {
    titleDisplay.style.outline = 'none';
    titleDisplay.style.cursor = 'default';
});

document.getElementById('toggleChat').addEventListener('click', () => {
    const sidebar = document.getElementById('chatSidebar');
    sidebar.classList.toggle('hidden');
});

document.getElementById('saveDoc').addEventListener('click', async () => {
    const content = tinymce.get('doc-text').getContent();
    const title = document.getElementById('doc-title-display').textContent.trim();
    const button = document.getElementById('saveDoc');
    const projectId = button.dataset.projectId;

    if (!title || !content) {
        alert('Заполните название и текст документа!');
        return;
    }

    try {
        const response = await fetch(`/api/project/${projectId}/document`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, content })
        });

        if (response.ok) {
            alert('Документ успешно сохранён!');
            window.location.href = `/project/${projectId}/documents`;
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (err) {
        console.error('Ошибка при отправке:', err);
        alert('Не удалось сохранить документ.');
    }
});