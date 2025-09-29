const confirmModal = {
    modal: document.getElementById('confirmModal'),
    titleEl: document.getElementById('modalTitle'),
    contentEl: document.getElementById('modalContent'),
    cancelBtn: document.getElementById('cancelButton'),
    confirmBtn: document.getElementById('confirmButton'),

    show({ title, content, url, confirmText = 'Confirm', cancelText = 'Cancel', onSuccess, onError }) {
        this.titleEl.textContent = title;
        this.contentEl.textContent = content;
        this.cancelBtn.textContent = cancelText;
        this.confirmBtn.textContent = confirmText;

        this.cancelBtn.onclick = () => this.hide();
        this.confirmBtn.onclick = () => {
            this.sendPostRequest(url, onSuccess, onError);
            this.hide();
        };

        this.modal.classList.remove('hidden');
        setTimeout(() => this.modal.classList.add('show'), 10);
    },

    hide() {
        this.modal.classList.remove('show');
        setTimeout(() => this.modal.classList.add('hidden'), 300);
    },

    sendPostRequest(url, onSuccess, onError) {
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCsrfToken(),
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (onSuccess) onSuccess(data);
                
            } else {
                if (onError) onError(data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (onError) onError({ message: 'An error occurred' });
        });
    },

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
};

// Close modal when clicking outside
confirmModal.modal.addEventListener('click', (e) => {
    if (e.target === confirmModal.modal) {
        confirmModal.hide();
    }
});