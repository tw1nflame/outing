document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.delete-button').forEach(button => {
        button.addEventListener('click', async (e) => {
            const documentId = e.target.dataset.documentId;
            const projectId = e.target.dataset.projectId; // Теперь project_id тоже из data-атрибута

            if (!confirm('Удалить этот документ?')) return;

            try {
                const response = await fetch(`/api/project/${projectId}/document/${documentId}`, {
                    method: 'DELETE',
                });

                if (response.ok) {
                    e.target.closest('.document-item').remove();
                    alert('Документ удалён.');
                } else {
                    const errorData = await response.json();
                    alert(`Ошибка: ${errorData.detail || 'Неизвестная ошибка'}`);
                }
            } catch (err) {
                console.error('Ошибка:', err);
                alert('Ошибка соединения с сервером');
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('index-form');
    const button = form.querySelector('.index-button');

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        button.disabled = true;
        button.textContent = 'Индексация...';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                button.textContent = 'Готово!';
                setTimeout(() => {
                    button.textContent = 'Проиндексировать';
                    button.disabled = false;
                }, 1500);
            } else if (response.status === 429) {
                const text = await response.text();
                alert('Индексация уже запущена, дождитесь её завершения');
                button.textContent = 'Проиндексировать';
                button.disabled = false;
            } else {
                button.textContent = 'Ошибка';
                setTimeout(() => {
                    button.textContent = 'Проиндексировать';
                    button.disabled = false;
                }, 2000);
            }
        } catch (error) {
            console.error('Ошибка при отправке запроса:', error);
            button.textContent = 'Ошибка сети';
            setTimeout(() => {
                button.textContent = 'Проиндексировать';
                button.disabled = false;
            }, 2000);
        }
    });
});
