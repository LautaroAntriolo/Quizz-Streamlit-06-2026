# 🎯 Quiz Platform — Streamlit

Plataforma para crear, compartir y jugar tests de opción múltiple. Incluye panel de administrador para cargar tests, sistema de puntaje, caché anti-repetición y resultados exportables.

---

## ✨ Funcionalidades

| Característica | Detalle |
|---|---|
| 🎮 Modo juego | Preguntas por secciones con scroll |
| ⏱ Temporizador opcional | Configurable por test en minutos |
| 📊 Sistema de puntaje | Porcentaje, correctas/total, detalle por sección |
| 🔒 Caché anti-repetición | Por sesión de navegador (sin login) |
| ⚙️ Panel admin | Carga, vista y eliminación de tests + historial de resultados |
| 📁 Formato .txt | Tests editables en cualquier editor de texto |

---

## 🚀 Instalación y uso local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/quiz-platform.git
cd quiz-platform
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la app

```bash
streamlit run app.py
```

La app abre en `http://localhost:8501`

---

## ☁️ Deploy en Streamlit Community Cloud (gratis)

1. Pusheá el repositorio a GitHub (público o privado).
2. Entrá a [share.streamlit.io](https://share.streamlit.io).
3. Hacé click en **"New app"**.
4. Seleccioná el repo, rama `main` y archivo `app.py`.
5. Click en **Deploy** — la URL pública estará lista en ~2 minutos.

> **Nota sobre persistencia**: En Streamlit Cloud, el sistema de archivos se resetea en cada redeploy. Si necesitás resultados permanentes, reemplazá `data/results.json` con una base de datos (ver sección de extensiones).

---

## 📝 Formato del archivo de test (.txt)

Los tests se guardan en la carpeta `tests/` con extensión `.txt`.

### Estructura básica

```
TÍTULO: Nombre del test
DESCRIPCIÓN: Descripción breve del test
TIEMPO_LIMITE: 30

---

SECCIÓN: Nombre de la primera sección

PREGUNTA: Texto completo de la pregunta
a) Opción A
b) Opción B
c) Opción C
d) Opción D
RESPUESTA: b

PREGUNTA: Otra pregunta (con solo 3 opciones también funciona)
a) Opción A
b) Opción B
c) Opción C
RESPUESTA: a

---

SECCIÓN: Segunda sección

PREGUNTA: Pregunta de la segunda sección
a) ...
b) ...
RESPUESTA: a
```

### Reglas del formato

| Campo | Obligatorio | Descripción |
|---|---|---|
| `TÍTULO:` | Sí | Nombre del test (también acepta `TITULO:`) |
| `DESCRIPCIÓN:` | No | Descripción breve |
| `TIEMPO_LIMITE:` | No | Minutos (0 o ausente = sin límite) |
| `SECCIÓN:` | No | Agrupa preguntas (también acepta `SECCION:`) |
| `PREGUNTA:` | Sí | Texto de la pregunta |
| `a) b) c) d)` | Sí | Opciones (mínimo 2, máximo 4) |
| `RESPUESTA:` | Sí | Letra de la opción correcta (a, b, c o d) |
| `---` | No | Separador visual (ignorado por el parser) |

---

## ⚙️ Panel de administrador

Accedé desde el botón **Admin** en la pantalla de inicio.

**Contraseña por defecto:** `admin1234`

Para cambiarla, editá la línea en `app.py`:
```python
ADMIN_PASSWORD = "admin1234"  # ← cambiá esto
```

### Funciones del admin

- **Cargar test**: Subí un `.txt` con el formato indicado
- **Tests activos**: Listado con opción de eliminar
- **Resultados**: Historial de todos los intentos (sesión, fecha, puntaje)

---

## 🔒 Sistema de caché (anti-repetición)

Cada usuario recibe un ID de sesión único generado al abrir la app. Una vez que enviá un test, ese test queda bloqueado para esa sesión — aunque recargues la página, verás tu resultado anterior en lugar del botón "Comenzar".

> El caché se basa en `st.session_state`, por lo que se resetea al cerrar el navegador. No requiere login ni cookies.

---

## 📊 Resultados

Los resultados se guardan en `data/results.json` con la siguiente estructura:

```json
{
  "session_id": "abc123",
  "test": "test_a.txt",
  "titulo": "Test A",
  "fecha": "2025-06-10T14:32:00",
  "pct": 85,
  "correct": 34,
  "total": 40,
  "elapsed_sec": 1820,
  "detail": [
    {
      "pregunta": "Texto...",
      "seccion": "Lógica",
      "elegida": "b",
      "correcta": "b",
      "ok": true
    }
  ]
}
```

---

## 🛠 Extensiones posibles

| Mejora | Cómo implementarla |
|---|---|
| Persistencia real | Reemplazar `results.json` con SQLite o [Supabase](https://supabase.com) |
| Link compartible por test | Usar `st.query_params` para pasar el nombre del test por URL |
| Ranking público | Agregar tabla de top puntajes con nombre voluntario |
| Modo aleatorio | Shuffle de preguntas con `random.shuffle()` |
| Contraseña en secrets | Usar `st.secrets["ADMIN_PASSWORD"]` para deploy seguro |

---

## 🗂 Estructura del proyecto

```
quiz-platform/
├── app.py                        ← Aplicación principal
├── requirements.txt              ← Dependencias
├── README.md                     ← Esta documentación
├── .gitignore
├── .streamlit/
│   └── config.toml              ← Tema visual
├── tests/
│   └── test_a_arte_y_video.txt  ← Test de ejemplo
└── data/
    └── results.json             ← Generado automáticamente
```

---

## 📄 Licencia

MIT — libre para usar, modificar y distribuir.
