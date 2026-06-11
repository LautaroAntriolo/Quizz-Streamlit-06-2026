import streamlit as st
import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
import re


# CONFIG

TESTS_DIR = Path("tests")
RESULTS_FILE = Path("data/results.json")
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]  # ← cambiá esto en producción

st.set_page_config(
    page_title="Quiz App",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ESTILOS
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fondo general */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    /* Tarjetas */
    .quiz-card {
        background: rgba(255,255,255,0.07);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
    }

    /* Hero */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #fff;
        text-align: center;
        line-height: 1.2;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.65);
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Badge de sección */
    .section-badge {
        display: inline-block;
        background: linear-gradient(90deg, #6c63ff, #48cae4);
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 50px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.8rem;
    }

    /* Pregunta número */
    .question-number {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.45);
        font-weight: 600;
        margin-bottom: 0.4rem;
    }

    /* Texto de pregunta */
    .question-text {
        font-size: 1.15rem;
        font-weight: 600;
        color: #fff;
        line-height: 1.6;
        margin-bottom: 1.2rem;
    }

    /* Opciones radio */
    div[data-testid="stRadio"] > label {
        display: none;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 0.5rem;
        display: flex;
        flex-direction: column;
    }

    /* Timer */
    .timer-bar {
        background: rgba(255,255,255,0.1);
        border-radius: 50px;
        height: 8px;
        width: 100%;
        margin: 0.5rem 0 1.5rem;
        overflow: hidden;
    }
    .timer-fill {
        height: 100%;
        border-radius: 50px;
        background: linear-gradient(90deg, #6c63ff, #48cae4);
        transition: width 1s linear;
    }

    /* Score badge */
    .score-display {
        font-size: 5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #6c63ff, #48cae4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
        margin: 1rem 0;
    }

    /* Progress */
    .progress-label {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.55);
        text-align: right;
        margin-bottom: 4px;
    }

    /* Botones personalizados */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(108, 99, 255, 0.4) !important;
    }

    /* Sidebar oscuro */
    [data-testid="stSidebar"] {
        background: rgba(15,12,41,0.95) !important;
    }
    [data-testid="stSidebar"] * {
        color: rgba(255,255,255,0.85) !important;
    }

    /* Result item */
    .result-item {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 0.7rem 1rem;
        margin: 0.4rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid transparent;
    }
    .result-correct { border-left-color: #4ade80; }
    .result-wrong   { border-left-color: #f87171; }

    /* Ocultar el menu de streamlit */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


# PARSEO DE TEST .TXT
def parse_test(filepath: Path) -> dict:
    """Parsea un archivo .txt con formato de test y retorna estructura dict."""
    text = filepath.read_text(encoding="utf-8")
    lines = [l.rstrip() for l in text.splitlines()]

    test = {
        "titulo": "Sin título",
        "descripcion": "",
        "tiempo_limite": 0,
        "secciones": [],
    }

    current_section = None
    current_question = None
    current_options = []
    i = 0

    def save_question():
        if current_question and current_options and current_section is not None:
            test["secciones"][current_section]["preguntas"].append({
                "texto": current_question["texto"],
                "opciones": list(current_options),
                "respuesta": current_question.get("respuesta", ""),
            })

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("TÍTULO:"):
            test["titulo"] = line[7:].strip()
        elif line.startswith("TITULO:"):
            test["titulo"] = line[7:].strip()
        elif line.startswith("DESCRIPCIÓN:") or line.startswith("DESCRIPCION:"):
            test["descripcion"] = line.split(":", 1)[1].strip()
        elif line.startswith("TIEMPO_LIMITE:"):
            try:
                test["tiempo_limite"] = int(line.split(":")[1].strip())
            except ValueError:
                test["tiempo_limite"] = 0

        elif line.startswith("SECCIÓN:") or line.startswith("SECCION:"):
            save_question()
            current_question = None
            current_options = []
            nombre_seccion = line.split(":", 1)[1].strip()
            test["secciones"].append({"nombre": nombre_seccion, "preguntas": []})
            current_section = len(test["secciones"]) - 1

        elif line.startswith("PREGUNTA:"):
            save_question()
            current_question = {"texto": line[9:].strip(), "respuesta": ""}
            current_options = []
            # Si no hay sección activa, creamos una default
            if current_section is None:
                test["secciones"].append({"nombre": "General", "preguntas": []})
                current_section = 0

        elif re.match(r'^[a-dA-D]\)', line) and current_question:
            current_options.append(line)

        elif line.startswith("RESPUESTA:") and current_question:
            current_question["respuesta"] = line.split(":", 1)[1].strip().lower()

        i += 1

    save_question()

    # Calcular total de preguntas
    test["total_preguntas"] = sum(
        len(s["preguntas"]) for s in test["secciones"]
    )
    return test


def get_available_tests() -> list[dict]:
    """Lista todos los tests .txt disponibles."""
    TESTS_DIR.mkdir(exist_ok=True)
    tests = []
    for f in sorted(TESTS_DIR.glob("*.txt")):
        try:
            data = parse_test(f)
            tests.append({
                "filename": f.name,
                "filepath": f,
                "titulo": data["titulo"],
                "descripcion": data["descripcion"],
                "total": data["total_preguntas"],
                "tiempo": data["tiempo_limite"],
            })
        except Exception as e:
            tests.append({
                "filename": f.name,
                "filepath": f,
                "titulo": f.stem.replace("_", " ").title(),
                "descripcion": f"Error al parsear: {e}",
                "total": 0,
                "tiempo": 0,
            })
    return tests

# PERSISTENCIA DE RESULTADOS
def load_results() -> list:
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    if RESULTS_FILE.exists():
        try:
            return json.loads(RESULTS_FILE.read_text())
        except Exception:
            return []
    return []


def save_result(entry: dict):
    results = load_results()
    results.append(entry)
    RESULTS_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2))

# CACHÉ ANTI-REPETICIÓN (browser fingerprint por sesión)
def get_session_id() -> str:
    """Genera un ID de sesión único para este navegador/sesión."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = hashlib.md5(
            str(time.time()).encode()
        ).hexdigest()[:12]
    return st.session_state.session_id


def check_already_submitted(test_filename: str) -> bool:
    sid = get_session_id()
    results = load_results()
    for r in results:
        if r.get("test") == test_filename and r.get("session_id") == sid:
            return True
    return False


def get_my_result(test_filename: str) -> dict | None:
    sid = get_session_id()
    results = load_results()
    for r in results:
        if r.get("test") == test_filename and r.get("session_id") == sid:
            return r
    return None


# INICIALIZACIÓN DE SESSION STATE

def init_quiz_state():
    defaults = {
        "page": "home",          # home | quiz | result | admin
        "selected_test": None,
        "test_data": None,
        "answers": {},            # idx → letra elegida
        "current_q": 0,
        "submitted": False,
        "start_time": None,
        "admin_logged": False,
        "flat_questions": [],     # lista plana de preguntas con info de sección
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v



# APLANAR PREGUNTAS

def flatten_questions(test_data: dict) -> list:
    flat = []
    for seccion in test_data["secciones"]:
        for q in seccion["preguntas"]:
            flat.append({**q, "seccion": seccion["nombre"]})
    return flat



# CALCULAR PUNTAJE

def calculate_score(answers: dict, questions: list) -> dict:
    correct = 0
    detail = []
    for idx, q in enumerate(questions):
        user_ans = answers.get(idx, "")
        is_correct = user_ans.lower() == q["respuesta"].lower()
        if is_correct:
            correct += 1
        detail.append({
            "pregunta": q["texto"][:80] + ("…" if len(q["texto"]) > 80 else ""),
            "seccion": q["seccion"],
            "elegida": user_ans,
            "correcta": q["respuesta"],
            "ok": is_correct,
        })
    total = len(questions)
    pct = round((correct / total * 100)) if total > 0 else 0
    return {"correct": correct, "total": total, "pct": pct, "detail": detail}



# PÁGINAS


def page_home():
    st.markdown('<div class="hero-title">🎯 Quiz Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Seleccioná un test para comenzar</div>', unsafe_allow_html=True)

    tests = get_available_tests()

    if not tests:
        st.markdown("""
        <div class="quiz-card" style="text-align:center; padding: 3rem;">
            <div style="font-size:3rem">📭</div>
            <h3 style="color:white">No hay tests disponibles</h3>
            <p style="color:rgba(255,255,255,0.5)">Un administrador debe cargar al menos un test .txt</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for t in tests:
            with st.container():
                st.markdown(f"""
                <div class="quiz-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <div style="font-size:1.3rem; font-weight:700; color:white; margin-bottom:0.3rem;">
                                📝 {t['titulo']}
                            </div>
                            <div style="color:rgba(255,255,255,0.55); font-size:0.9rem; margin-bottom:0.8rem;">
                                {t['descripcion'][:120] + "…" if len(t['descripcion']) > 120 else t['descripcion']}
                            </div>
                            <div style="display:flex; gap:1rem;">
                                <span style="background:rgba(108,99,255,0.3); color:#a89fff; padding:3px 12px; border-radius:50px; font-size:0.8rem; font-weight:600;">
                                    {t['total']} preguntas
                                </span>
                                {"" if t['tiempo'] == 0 else f'<span style="background:rgba(72,202,228,0.2); color:#7dd3fc; padding:3px 12px; border-radius:50px; font-size:0.8rem; font-weight:600;">⏱ {t["tiempo"]} min</span>'}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                already = check_already_submitted(t["filename"])
                col1, col2 = st.columns([3, 1])
                with col2:
                    if already:
                        if st.button("Ver mi resultado", key=f"ver_{t['filename']}",
                                     use_container_width=True, type="secondary"):
                            result = get_my_result(t["filename"])
                            st.session_state.score_data = result
                            st.session_state.selected_test = t
                            st.session_state.page = "result"
                            st.rerun()
                    else:
                        if st.button("▶ Comenzar", key=f"start_{t['filename']}",
                                     use_container_width=True, type="primary"):
                            start_quiz(t)

    st.markdown("---")
    col_adm = st.columns([4, 1])[1]
    with col_adm:
        if st.button("⚙ Admin", use_container_width=True, key="go_admin"):
            st.session_state.page = "admin"
            st.rerun()


def start_quiz(test_info: dict):
    data = parse_test(test_info["filepath"])
    flat = flatten_questions(data)
    st.session_state.selected_test = test_info
    st.session_state.test_data = data
    st.session_state.flat_questions = flat
    st.session_state.answers = {}
    st.session_state.current_q = 0
    st.session_state.submitted = False
    st.session_state.start_time = time.time()
    st.session_state.page = "quiz"
    st.rerun()


def page_quiz():
    test_info = st.session_state.selected_test
    questions = st.session_state.flat_questions
    total_q = len(questions)

    # Encabezado
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Inicio", key="back_home"):
            st.session_state.page = "home"
            st.rerun()
    with col_title:
        st.markdown(
            f'<div style="color:white; font-weight:700; font-size:1.1rem; padding-top:6px;">'
            f'📝 {test_info["titulo"]}</div>',
            unsafe_allow_html=True,
        )

    # Timer (si aplica)
    tiempo_limite = test_info.get("tiempo", 0)
    if tiempo_limite and tiempo_limite > 0 and st.session_state.start_time:
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, tiempo_limite * 60 - elapsed)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        pct_remaining = remaining / (tiempo_limite * 60) * 100
        color = "#4ade80" if pct_remaining > 50 else "#facc15" if pct_remaining > 20 else "#f87171"
        st.markdown(f"""
        <div style="color:rgba(255,255,255,0.6); font-size:0.85rem; margin-top:0.5rem;">
            ⏱ Tiempo restante: <strong style="color:{color}">{mins:02d}:{secs:02d}</strong>
        </div>
        <div class="timer-bar">
            <div class="timer-fill" style="width:{pct_remaining}%; background: linear-gradient(90deg, {color}, {color}88);"></div>
        </div>
        """, unsafe_allow_html=True)

        if remaining == 0 and not st.session_state.submitted:
            finish_quiz()
            return

    # Renderizado de TODAS las preguntas en scroll
    st.markdown(
        f'<div class="progress-label">Respondidas: '
        f'{len(st.session_state.answers)} / {total_q}</div>',
        unsafe_allow_html=True,
    )
    st.progress(len(st.session_state.answers) / total_q if total_q > 0 else 0)

    current_section = None
    for idx, q in enumerate(questions):
        # Header de sección cuando cambia
        if q["seccion"] != current_section:
            current_section = q["seccion"]
            st.markdown(
                f'<div style="margin-top:1.5rem;"><span class="section-badge">📌 {current_section}</span></div>',
                unsafe_allow_html=True,
            )

        # Tarjeta de pregunta
        answered = idx in st.session_state.answers
        border_color = "rgba(74, 222, 128, 0.5)" if answered else "rgba(255,255,255,0.1)"

        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.06);
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 1.3rem 1.5rem;
            margin: 0.7rem 0;
        ">
            <div class="question-number">Pregunta {idx + 1} de {total_q}</div>
            <div class="question-text">{q['texto']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Opciones de respuesta
        options_map = {}
        options_display = []
        for opt in q["opciones"]:
            letter = opt[0].lower()
            display = opt
            options_map[display] = letter
            options_display.append(display)

        prev_answer = st.session_state.answers.get(idx)
        # Encontrar el índice previo
        default_idx = None
        if prev_answer:
            for i, d in enumerate(options_display):
                if d[0].lower() == prev_answer:
                    default_idx = i
                    break

        selection = st.radio(
            label=f"q_{idx}",
            options=options_display,
            index=default_idx,
            key=f"radio_{idx}",
            label_visibility="collapsed",
        )
        if selection:
            st.session_state.answers[idx] = options_map[selection]

        st.markdown('<div style="margin-bottom: 0.5rem;"></div>', unsafe_allow_html=True)

    # Botón de envío
    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    answered_count = len(st.session_state.answers)
    all_answered = answered_count == total_q

    if not all_answered:
        st.info(f"⚠️ Faltan {total_q - answered_count} preguntas por responder.")

    if st.button(
        "✅ Enviar respuestas" if all_answered else f"Enviar ({answered_count}/{total_q} respondidas)",
        type="primary",
        use_container_width=True,
        key="submit_quiz",
    ):
        finish_quiz()


def finish_quiz():
    questions = st.session_state.flat_questions
    score_data = calculate_score(st.session_state.answers, questions)

    elapsed = int(time.time() - st.session_state.start_time) if st.session_state.start_time else 0

    entry = {
        "session_id": get_session_id(),
        "test": st.session_state.selected_test["filename"],
        "titulo": st.session_state.selected_test["titulo"],
        "fecha": datetime.now().isoformat(),
        "pct": score_data["pct"],
        "correct": score_data["correct"],
        "total": score_data["total"],
        "elapsed_sec": elapsed,
        "detail": score_data["detail"],
    }
    save_result(entry)
    st.session_state.score_data = entry
    st.session_state.submitted = True
    st.session_state.page = "result"
    st.rerun()

def page_result():
    score = st.session_state.get("score_data", {})
    pct = score.get("pct", 0)
    correct = score.get("correct", 0)
    total = score.get("total", 0)
    elapsed = score.get("elapsed_sec", 0)
    detail = score.get("detail", [])

    # Emoji según puntaje
    if pct >= 90:
        emoji, msg, color = "🏆", "¡Excelente!", "#4ade80"
    elif pct >= 70:
        emoji, msg, color = "🎉", "¡Muy bien!", "#a3e635"
    elif pct >= 50:
        emoji, msg, color = "📈", "Buen intento", "#facc15"
    else:
        emoji, msg, color = "💪", "¡A seguir practicando!", "#f87171"

    st.markdown(f"""
    <div class="quiz-card" style="text-align:center; padding: 2.5rem;">
        <div style="font-size: 4rem;">{emoji}</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: white; margin: 0.5rem 0;">{msg}</div>
        <div class="score-display">{pct}%</div>
        <div style="color: rgba(255,255,255,0.6); font-size: 1rem; margin-top: 0.5rem;">
            {correct} correctas de {total} preguntas
            {"&nbsp;|&nbsp; ⏱ " + str(elapsed // 60) + "m " + str(elapsed % 60) + "s" if elapsed > 0 else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Detalle por sección
    if detail:
        st.markdown('<div style="margin-top:1.5rem; color: white; font-weight: 700; font-size: 1.1rem;">📋 Detalle de respuestas</div>', unsafe_allow_html=True)

        sections_done = {}
        for d in detail:
            sec = d["seccion"]
            if sec not in sections_done:
                sections_done[sec] = []
            sections_done[sec].append(d)

        for sec_name, items in sections_done.items():
            sec_correct = sum(1 for i in items if i["ok"])
            with st.expander(f"📌 {sec_name}  —  {sec_correct}/{len(items)} correctas"):
                for item in items:
                    icon = "✅" if item["ok"] else "❌"
                    clase = "result-correct" if item["ok"] else "result-wrong"
                    info = (
                        f'Tu resp: <strong>{item["elegida"].upper()}</strong>'
                        if item["ok"]
                        else f'Tu resp: <strong>{item["elegida"].upper()}</strong> | Correcta: <strong>{item["correcta"].upper()}</strong>'
                    )
                    st.markdown(f"""
                    <div class="result-item {clase}">
                        <span style="color:rgba(255,255,255,0.85); font-size:0.9rem;">{icon} {item['pregunta']}</span>
                        <span style="color:rgba(255,255,255,0.5); font-size:0.8rem; white-space:nowrap; margin-left:1rem;">{info}</span>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    if st.button("🏠 Volver al inicio", type="primary", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

def page_admin():
    # Login
    if not st.session_state.admin_logged:
        st.markdown('<div class="hero-title">⚙️ Panel Admin</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">Ingresá la contraseña para continuar</div>', unsafe_allow_html=True)
        col = st.columns([1, 2, 1])[1]
        with col:
            pwd = st.text_input("Contraseña", type="password", key="admin_pwd_input")
            if st.button("Ingresar", type="primary", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.admin_logged = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
        st.markdown("---")
        if st.button("← Volver", key="back_from_login"):
            st.session_state.page = "home"
            st.rerun()
        return

    # ── Admin autenticado ──
    st.markdown('<div class="hero-title">⚙️ Panel Administrador</div>', unsafe_allow_html=True)

    col_back, col_logout = st.columns([4, 1])
    with col_back:
        if st.button("← Inicio", key="admin_home"):
            st.session_state.page = "home"
            st.rerun()
    with col_logout:
        if st.button("Cerrar sesión", key="logout"):
            st.session_state.admin_logged = False
            st.session_state.page = "home"
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["📤 Cargar test", "📋 Tests activos", "📊 Resultados"])

    # ─────────────────────────────────
    # TAB 1: Subir test
    # ─────────────────────────────────
    with tab1:
        st.markdown("### Subir nuevo test (.txt)")
        st.markdown("""
        <div class="quiz-card" style="font-size:0.9rem; color:rgba(255,255,255,0.7);">
        <strong style="color:white">Formato del archivo .txt:</strong><br><br>
        <code>
        TÍTULO: Nombre del test<br>
        DESCRIPCIÓN: Descripción breve<br>
        TIEMPO_LIMITE: 30  # minutos (0 = sin límite)<br><br>
        ---<br><br>
        SECCIÓN: Nombre de sección<br><br>
        PREGUNTA: Texto de la pregunta<br>
        a) Opción A<br>
        b) Opción B<br>
        c) Opción C<br>
        d) Opción D<br>
        RESPUESTA: b<br>
        </code>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader("Seleccioná el archivo .txt", type=["txt"])
        if uploaded:
            TESTS_DIR.mkdir(exist_ok=True)
            save_path = TESTS_DIR / uploaded.name
            if save_path.exists():
                st.warning(f"⚠️ Ya existe un test con el nombre `{uploaded.name}`. Se sobreescribirá.")
            save_path.write_bytes(uploaded.read())

            # Verificar que parsea bien
            try:
                data = parse_test(save_path)
                st.success(
                    f"✅ Test **{data['titulo']}** cargado correctamente "
                    f"({data['total_preguntas']} preguntas en {len(data['secciones'])} secciones)"
                )
            except Exception as e:
                st.error(f"❌ Error al parsear el test: {e}")
                save_path.unlink(missing_ok=True)

    # ─────────────────────────────────
    # TAB 2: Tests activos
    # ─────────────────────────────────
    with tab2:
        st.markdown("### Tests disponibles")
        tests = get_available_tests()
        if not tests:
            st.info("No hay tests cargados aún.")
        for t in tests:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class="quiz-card" style="padding:1rem 1.5rem;">
                    <strong style="color:white">{t['titulo']}</strong>
                    <span style="color:rgba(255,255,255,0.45); font-size:0.85rem; margin-left:0.5rem;">— {t['filename']}</span><br>
                    <span style="color:rgba(255,255,255,0.5); font-size:0.85rem;">{t['total']} preguntas
                    {"| ⏱ " + str(t['tiempo']) + " min" if t['tiempo'] > 0 else ""}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)
                if st.button("🗑 Eliminar", key=f"del_{t['filename']}"):
                    Path(t["filepath"]).unlink(missing_ok=True)
                    st.success(f"Eliminado: {t['filename']}")
                    st.rerun()

    # ─────────────────────────────────
    # TAB 3: Resultados
    # ─────────────────────────────────
    with tab3:
        st.markdown("### Resultados registrados")
        results = load_results()
        if not results:
            st.info("Aún no hay resultados.")
        else:
            # Resumen
            col1, col2, col3 = st.columns(3)
            col1.metric("Total intentos", len(results))
            avg_pct = round(sum(r.get("pct", 0) for r in results) / len(results))
            col2.metric("Promedio", f"{avg_pct}%")
            perfect = sum(1 for r in results if r.get("pct", 0) == 100)
            col3.metric("Puntajes perfectos", perfect)

            st.markdown("---")

            # Tabla de resultados
            for r in reversed(results):
                fecha = r.get("fecha", "")[:16].replace("T", " ")
                sid = r.get("session_id", "?")[:6]
                pct = r.get("pct", 0)
                color = "#4ade80" if pct >= 70 else "#facc15" if pct >= 50 else "#f87171"
                st.markdown(f"""
                <div class="quiz-card" style="padding:0.8rem 1.2rem; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="color:white; font-weight:600;">{r.get('titulo','')}</span>
                        <span style="color:rgba(255,255,255,0.4); font-size:0.8rem; margin-left:0.5rem;">#{sid}</span><br>
                        <span style="color:rgba(255,255,255,0.5); font-size:0.8rem;">{fecha}</span>
                    </div>
                    <span style="color:{color}; font-size:1.3rem; font-weight:800;">{pct}%</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div style="margin-top:1rem"></div>', unsafe_allow_html=True)
            if st.button("🗑 Borrar todos los resultados", type="secondary"):
                RESULTS_FILE.write_text("[]")
                st.success("Resultados borrados.")
                st.rerun()



# MAIN

def main():
    inject_css()
    init_quiz_state()
    get_session_id()  # asegura que exista

    page = st.session_state.page

    if page == "home":
        page_home()
    elif page == "quiz":
        page_quiz()
    elif page == "result":
        page_result()
    elif page == "admin":
        page_admin()


if __name__ == "__main__":
    main()
