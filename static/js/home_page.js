let editingProjectId = null;
const input = document.getElementById('projectName');
const button = document.getElementById('formButton');
const form = document.querySelector('.form');
const projectList = document.getElementById('projectList');

form.addEventListener('submit', handleSubmit);

async function handleSubmit(event) {
    event.preventDefault();
    const name = input.value.trim();
    if (!name) return;

    if (editingProjectId) {
        // Переименование
        try {
            const response = await fetch(`/api/projects/${editingProjectId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: name })
            });
            if (response.ok) {
                const updated = await response.json();
                const card = document.querySelector(`[data-id="${editingProjectId}"]`);
                const link = card.querySelector('.project-link');
                link.textContent = updated.title;
            }
        } catch (err) {
            console.error('Ошибка при переименовании:', err);
        }

        input.value = '';
        button.textContent = 'Создать';
        editingProjectId = null;

    } else {
        // Создание нового проекта
        try {
            const response = await fetch('/api/projects/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: name })
            });
            if (response.ok) {
                const created = await response.json();
                addProjectCard(created.id, created.title);
                input.value = '';
            }
        } catch (err) {
            console.error('Ошибка при создании проекта:', err);
        }
    }
}

function startRename(id) {
    const card = document.querySelector(`[data-id="${id}"]`);
    const link = card.querySelector('.project-link');
    input.value = link.textContent;
    editingProjectId = id;
    button.textContent = 'Сохранить';
    input.focus();
}

async function deleteProject(id) {
    if (!confirm('Удалить проект?')) return;

    try {
        const response = await fetch(`/api/projects/${id}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            const card = document.querySelector(`[data-id="${id}"]`);
            card.remove();

            if (editingProjectId === id) {
                editingProjectId = null;
                input.value = '';
                button.textContent = 'Создать';
            }
        }
    } catch (err) {
        console.error('Ошибка при удалении проекта:', err);
    }
}

function addProjectCard(id, title) {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.dataset.id = id;

    const link = document.createElement('a');
    link.className = 'project-link';
    link.href = `project/${id}`;
    link.textContent = title;

    const actions = document.createElement('div');
    actions.className = 'project-actions';

    const renameBtn = document.createElement('button');
    renameBtn.textContent = 'Переименовать';
    renameBtn.onclick = () => startRename(id);

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Удалить';
    deleteBtn.onclick = () => deleteProject(id);

    actions.appendChild(renameBtn);
    actions.appendChild(deleteBtn);

    card.appendChild(link);
    card.appendChild(actions);

    projectList.appendChild(card);
}
