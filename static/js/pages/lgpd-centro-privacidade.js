document.addEventListener('DOMContentLoaded', function() {
	const notify = (kind, message) => {
		if (window.showToast) {
			window.showToast(kind, message, kind === 'error' ? 4600 : 3200);
			return;
		}
		const logger = kind === 'error' ? console.error : console.info;
		logger(message);
	};

	const tabButtons = document.querySelectorAll('[data-lgpd-tab]');
	tabButtons.forEach((btn) => {
		btn.addEventListener('shown.bs.tab', function() {
			const tab = btn.getAttribute('data-lgpd-tab');
			const url = new URL(window.location.href);
			url.searchParams.set('tab', tab);
			window.history.replaceState({}, '', url.toString());
		});
	});

	const dataRequestForm = document.querySelector('.js-data-access-form');
	if (dataRequestForm) {
		dataRequestForm.addEventListener('submit', async function(event) {
			event.preventDefault();
			const submitBtn = dataRequestForm.querySelector('button[type="submit"]');
			const requestOpenNote = document.getElementById('request-open-note');
			const requestHistoryWrap = document.getElementById('request-history-table-wrap');
			const requestHistoryBody = document.getElementById('request-history-body');
			const requestEmptyState = document.getElementById('request-empty-state');
			const feedbackNode = document.getElementById('request-live-feedback');
			const originalLabel = submitBtn ? submitBtn.textContent.trim() : '';

			if (submitBtn) {
				submitBtn.disabled = true;
				submitBtn.textContent = 'Enviando...';
			}

			try {
				const response = await fetch(dataRequestForm.action, {
					method: 'POST',
					headers: {
						'X-Requested-With': 'XMLHttpRequest',
					},
					body: new FormData(dataRequestForm),
				});

				const payload = await response.json();
				if (!response.ok || !payload.ok) {
					throw new Error(payload.error || 'Nao foi possivel registrar a solicitacao.');
				}

				if (payload.request && requestHistoryBody) {
					const row = document.createElement('tr');
					const fileCell = payload.request.file_url
						? `<a href="${payload.request.file_url}" class="btn btn-sm btn-outline-light" target="_blank" rel="noopener noreferrer">Baixar</a>`
						: '-';

					row.innerHTML = `
						<td>${payload.request.created_at}</td>
						<td><span class="status-pill status-pill--${payload.request.status}">${payload.request.status_label}</span></td>
						<td>${payload.request.processed_at || '-'}</td>
						<td>${fileCell}</td>
					`;
					requestHistoryBody.prepend(row);

					if (requestHistoryWrap) {
						requestHistoryWrap.classList.remove('d-none');
					}
					if (requestEmptyState) {
						requestEmptyState.classList.add('d-none');
					}
				}

				if (feedbackNode) {
					feedbackNode.textContent = payload.message;
					feedbackNode.classList.remove('d-none', 'request-live-feedback--error');
					feedbackNode.classList.add('request-live-feedback--ok');
				}
				notify('success', payload.message || 'Solicitacao enviada com sucesso.');
				dataRequestForm.reset();
				if (submitBtn) {
					submitBtn.disabled = true;
				}
				if (requestOpenNote) {
					requestOpenNote.classList.remove('d-none');
				}
			} catch (error) {
				if (feedbackNode) {
					feedbackNode.textContent = error.message;
					feedbackNode.classList.remove('d-none', 'request-live-feedback--ok');
					feedbackNode.classList.add('request-live-feedback--error');
				}
				notify('error', error.message);
				if (submitBtn && originalLabel) {
					submitBtn.disabled = false;
				}
			} finally {
				if (submitBtn && originalLabel) {
					submitBtn.textContent = originalLabel;
				}
			}
		});
	}

	const deletionForm = document.querySelector('.js-account-deletion-form');
	if (deletionForm) {
		deletionForm.addEventListener('submit', async function(event) {
			event.preventDefault();
			const submitBtn = deletionForm.querySelector('button[type="submit"]');
			const openNote = document.getElementById('deletion-open-note');
			const historyWrap = document.getElementById('deletion-history-table-wrap');
			const historyBody = document.getElementById('deletion-history-body');
			const emptyState = document.getElementById('deletion-empty-state');
			const feedbackNode = document.getElementById('deletion-live-feedback');
			const originalLabel = submitBtn ? submitBtn.textContent.trim() : '';

			if (submitBtn) {
				submitBtn.disabled = true;
				submitBtn.textContent = 'Enviando...';
			}

			try {
				const response = await fetch(deletionForm.action, {
					method: 'POST',
					headers: {
						'X-Requested-With': 'XMLHttpRequest',
					},
					body: new FormData(deletionForm),
				});

				const payload = await response.json();
				if (!response.ok || !payload.ok) {
					throw new Error(payload.error || 'Nao foi possivel registrar a solicitacao de exclusao.');
				}

				if (payload.request && historyBody) {
					const row = document.createElement('tr');
					row.id = `deletion-row-${payload.request.id}`;
					row.innerHTML = `
						<td>${payload.request.created_at}</td>
						<td><span class="status-pill status-pill--${payload.request.status}">${payload.request.status_label}</span></td>
						<td>${payload.request.expires_at}</td>
						<td>-</td>
					`;
					historyBody.prepend(row);

					if (historyWrap) {
						historyWrap.classList.remove('d-none');
					}
					if (emptyState) {
						emptyState.classList.add('d-none');
					}
				}

				if (feedbackNode) {
					feedbackNode.textContent = payload.message;
					feedbackNode.classList.remove('d-none', 'request-live-feedback--error');
					feedbackNode.classList.add('request-live-feedback--ok');
				}
				if (openNote) {
					openNote.classList.remove('d-none');
				}
				deletionForm.reset();
				notify('success', payload.message || 'Solicitacao de exclusao registrada.');
			} catch (error) {
				if (feedbackNode) {
					feedbackNode.textContent = error.message;
					feedbackNode.classList.remove('d-none', 'request-live-feedback--ok');
					feedbackNode.classList.add('request-live-feedback--error');
				}
				notify('error', error.message || 'Falha ao solicitar exclusao.');
				if (submitBtn) {
					submitBtn.disabled = false;
				}
			} finally {
				if (submitBtn) {
					submitBtn.textContent = originalLabel || 'Solicitar Exclusao';
				}
			}
		});
	}

	const cancelForms = document.querySelectorAll('.js-deletion-cancel-form');
	cancelForms.forEach((form) => {
		form.addEventListener('submit', async function(event) {
			event.preventDefault();
			const submitBtn = form.querySelector('button[type="submit"]');
			const requestId = form.dataset.requestId;
			if (submitBtn) {
				submitBtn.disabled = true;
				submitBtn.textContent = 'Cancelando...';
			}

			try {
				const response = await fetch(form.action, {
					method: 'POST',
					headers: {
						'X-Requested-With': 'XMLHttpRequest',
					},
					body: new FormData(form),
				});
				const payload = await response.json();
				if (!response.ok || !payload.ok) {
					throw new Error(payload.error || 'Falha ao cancelar solicitacao.');
				}

				const row = document.getElementById(`deletion-row-${requestId}`);
				if (row) {
					const statusCell = row.children[1];
					const actionCell = row.children[3];
					if (statusCell) {
						statusCell.innerHTML = '<span class="status-pill status-pill--canceled">Cancelada</span>';
					}
					if (actionCell) {
						actionCell.textContent = '-';
					}
				}

				notify('success', payload.message || 'Solicitacao cancelada.');
			} catch (error) {
				notify('error', error.message || 'Nao foi possivel cancelar a solicitacao.');
				if (submitBtn) {
					submitBtn.disabled = false;
					submitBtn.textContent = 'Cancelar';
				}
			}
		});
	});

	const statusClassMap = {
		accepted: {
			mandatory: 'status-pill status-pill--completed',
			cookies: 'status-pill status-pill--processing',
			label: 'Aceito',
		},
		rejected: {
			mandatory: 'status-pill status-pill--denied',
			cookies: 'status-pill status-pill--pending',
			label: 'Nao aceito',
		},
	};

	const consentForms = document.querySelectorAll('.js-consent-form');
	consentForms.forEach((form) => {
		form.addEventListener('submit', async function(event) {
			event.preventDefault();

			const submitBtn = form.querySelector('button[type="submit"]');
			const originalLabel = submitBtn ? submitBtn.textContent.trim() : '';
			const formData = new FormData(form);
			const consentType = formData.get('consent_type');
			const accepted = ['1', 'true', 'True', 'on'].includes(String(formData.get('accepted')));
			const itemNode = form.closest('[data-consent-item]');
			const statusNode = itemNode ? itemNode.querySelector('[data-consent-status]') : null;
			const metaNode = itemNode ? itemNode.querySelector('[data-consent-meta]') : null;
			const isCookies = consentType === 'cookies';

			if (submitBtn) {
				submitBtn.disabled = true;
				submitBtn.textContent = 'Salvando...';
			}

			try {
				const response = await fetch(form.action, {
					method: 'POST',
					headers: {
						'X-Requested-With': 'XMLHttpRequest',
					},
					body: formData,
				});

				const payload = await response.json();
				if (!response.ok || !payload.ok) {
					throw new Error(payload.error || 'Falha ao atualizar consentimento.');
				}

				if (statusNode) {
					const targetMap = accepted ? statusClassMap.accepted : statusClassMap.rejected;
					statusNode.className = isCookies ? targetMap.cookies : targetMap.mandatory;
					statusNode.textContent = targetMap.label;
				}

				if (metaNode) {
					if (consentType === 'cookies') {
						metaNode.textContent = `Ultima escolha em ${payload.timestamp_label}`;
					} else {
						metaNode.textContent = `Versao ${payload.document_version || '1.0'} · ${payload.timestamp_label}`;
					}
				}

				if (!isCookies && accepted && itemNode) {
					const actionsNode = itemNode.querySelector('.consent-buttons--single');
					if (actionsNode) {
						actionsNode.innerHTML = '<span class="lgpd-btn lgpd-btn--sm lgpd-btn--done" data-consent-accepted-badge>Aceito</span>';
					}
				}

				if (isCookies && itemNode) {
					const acceptBtn = itemNode.querySelector('[data-consent-accept-btn]');
					if (acceptBtn) {
						acceptBtn.disabled = accepted;
						acceptBtn.textContent = accepted ? 'Aceito' : 'Aceitar';
					}
				}

				notify('success', payload.message || 'Consentimento atualizado.');
			} catch (error) {
				notify('error', error.message || 'Falha ao atualizar consentimento.');
			} finally {
				if (submitBtn) {
					const mustKeepDisabled = isCookies && accepted;
					submitBtn.disabled = mustKeepDisabled;
					submitBtn.textContent = mustKeepDisabled ? 'Aceito' : (originalLabel || 'Aceitar');
				}
			}
		});
	});
});
