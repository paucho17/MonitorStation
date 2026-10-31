<!--
	Chatbot: widget flotante que consulta la API auxiliar (/aux/chatbot/consultar).
	No depende de servicios externos. Muestra el campo "respuesta" del JSON.
-->
<script>
	import { api_chatbot } from '#lib/servicios/datos.js';

	const SUGERENCIAS = [
		'Que es el pH y cual es su rango normal?',
		'Cuando se riega automaticamente?',
		'Que significa una alerta critica?'
	];

	let abierto = $state(false);
	let texto = $state('');
	let enviando = $state(false);
	let mensajes = $state([
		{ quien: 'bot', texto: 'Hola, soy el asistente de IoT-Mangrove. Puedo explicarte las variables, sus umbrales y el riego.' }
	]);
	let registro = $state();

	async function preguntar(pregunta) {
		const q = pregunta.trim();
		if (!q || enviando) return;
		mensajes.push({ quien: 'usuario', texto: q });
		texto = '';
		enviando = true;
		try {
			const r = await api_chatbot.preguntar(q);
			mensajes.push({ quien: 'bot', texto: r.respuesta ?? 'No tengo una respuesta para eso.' });
		} catch {
			mensajes.push({ quien: 'bot', texto: 'No pude consultar el asistente en este momento.' });
		} finally {
			enviando = false;
			queueMicrotask(() => registro && (registro.scrollTop = registro.scrollHeight));
		}
	}
</script>

<button class="lanzador" aria-label="Abrir asistente" aria-expanded={abierto} onclick={() => (abierto = !abierto)}>
	{abierto ? '×' : '?'}
</button>

{#if abierto}
	<div class="panel" role="dialog" aria-label="Asistente de IoT-Mangrove">
		<header><strong>Asistente IoT-Mangrove</strong></header>
		<div class="registro" bind:this={registro} role="log" aria-live="polite">
			{#each mensajes as m, i (i)}
				<div class="msg {m.quien}">{m.texto}</div>
			{/each}
			{#if enviando}<div class="msg bot">Escribiendo...</div>{/if}
			{#if mensajes.length === 1}
				<div class="sugerencias">
					{#each SUGERENCIAS as s (s)}
						<button type="button" onclick={() => preguntar(s)}>{s}</button>
					{/each}
				</div>
			{/if}
		</div>
		<form onsubmit={(e) => { e.preventDefault(); preguntar(texto); }}>
			<input bind:value={texto} maxlength="300" placeholder="Escribe tu pregunta" aria-label="Pregunta" />
			<button type="submit" disabled={enviando}>Enviar</button>
		</form>
	</div>
{/if}

<style>
	.lanzador {
		position: fixed;
		right: 1rem;
		bottom: 1rem;
		width: 3.2rem;
		height: 3.2rem;
		border-radius: 50%;
		border: 0;
		background: var(--color-primary);
		color: #fff;
		font-size: 1.5rem;
		font-weight: 700;
		box-shadow: var(--shadow);
		cursor: pointer;
		z-index: 30;
	}
	.panel {
		position: fixed;
		right: 1rem;
		bottom: 5rem;
		width: min(22rem, calc(100vw - 2rem));
		height: min(30rem, 70vh);
		display: flex;
		flex-direction: column;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		z-index: 30;
	}
	header {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--color-border);
	}
	.registro {
		flex: 1;
		overflow-y: auto;
		padding: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.msg {
		max-width: 85%;
		padding: 0.5rem 0.75rem;
		border-radius: 0.75rem;
		white-space: pre-wrap;
		font-size: 0.92rem;
	}
	.bot {
		align-self: flex-start;
		background: var(--color-bg);
	}
	.usuario {
		align-self: flex-end;
		background: var(--color-primary);
		color: #fff;
	}
	.sugerencias {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}
	.sugerencias button {
		text-align: left;
		padding: 0.4rem 0.6rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		background: var(--color-surface);
		color: var(--color-text);
		font: inherit;
		font-size: 0.85rem;
		cursor: pointer;
	}
	form {
		display: flex;
		gap: 0.4rem;
		padding: 0.6rem;
		border-top: 1px solid var(--color-border);
	}
	input {
		flex: 1;
		padding: 0.5rem 0.7rem;
		font: inherit;
		color: var(--color-text);
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
	}
	form button {
		padding: 0.5rem 0.9rem;
		border: 0;
		border-radius: var(--radius);
		background: var(--color-primary);
		color: #fff;
		font: inherit;
		font-weight: 600;
		cursor: pointer;
	}
	form button:disabled {
		opacity: 0.6;
	}
</style>
