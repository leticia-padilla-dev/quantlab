# QuantLab Landing

Landing estatica preparada para preview local y publicacion en GitHub Pages.

## Governance

- Source of truth: `../docs/brand-guidelines.md`
- Landing workflow: `../docs/landing-governance.md`
- Folder-specific rules: `./AGENTS.md`

If a copy, brand, or layout change touches the public position of QuantLab Research, update the canonical docs first and the landing surface second.

## Estructura

- `index.html`
- `styles.css`
- `app.js`

## Preview local

La landing no pertenece al paquete `desktop/`. Es una superficie web estatica
autocontenida en `landing/`.

Desde la raiz del repo:

```powershell
cd C:\dev\quantlab\landing
npm run dev
```

URL local:

```text
http://127.0.0.1:4173/
```

El puerto puede cambiarse con `PORT`:

```powershell
$env:PORT=5174
npm run dev
```

No hace falta `npm install`: los scripts usan solo modulos nativos de Node.

## Validacion local antes de PR

```powershell
cd C:\dev\quantlab\landing
npm run build
npm run lint
git diff --check
```

`npm run build` y `npm run lint` ejecutan la misma validacion estatica: archivos
requeridos, referencias CSS/JS y copy minima de marca. No generan assets.

Checklist visual:

- La pagina carga en `http://127.0.0.1:4173/`.
- La direccion sigue siendo local-first, evidence-first, reproducible, traceable
  y supervised.
- La landing no parece una fintech dashboard, trading app o AI-hype page.
- Revisar desktop y viewport estrecho antes de abrir PR.

## Deploy

El workflow [pages.yml](../.github/workflows/pages.yml) publica el contenido de `landing/` en GitHub Pages cuando hay cambios en `main`.

Requisito del repositorio:

- GitHub Pages debe estar configurado para desplegar desde **GitHub Actions**.
