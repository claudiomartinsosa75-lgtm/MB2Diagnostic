import base64
import json
import os
import ssl
import smtplib
import urllib.request
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler

# ── Configuración ──────────────────────────────────────────────────────────────
CALENDLY_URL = "https://calendly.com/mb2managementteams-info/30min"

# ── Tabla de puntuaciones ──────────────────────────────────────────────────────
ANSWER_SCORES = {
    # P1 - Organigrama
    "No tenemos organigrama": 0,
    "Existe pero está desactualizado o solo administrativo": 2,
    "Actualizado pero sin jefes con poder de decisión real": 3,
    "Organigrama funcional con jefes claros y delegación efectiva": 5,
    # P2 - Rotación
    "No lo sé / No lo mido": 0,
    "Más del 50%": 0,
    "Entre 30% y 50%": 2,
    "Menos del 30%": 5,
    # P3 - Formación
    "Formación solo reactiva (cuando surge problema)": 0,
    "Plan existe pero no se cumple": 2,
    "Plan anual definido pero sin seguimiento sistemático": 3,
    "Plan calendarizado + evaluación post-formación + KPIs": 5,
    # P4 - Horarios
    "Caótico / improvisado semana a semana": 0,
    "Excel o papel, sin sistema perpetuo": 2,
    "Sistema digital pero sin optimización de libranzas": 3,
    "Horarios perpetuos con bolsa de horas y libranzas equilibradas": 5,
    # P5 - Protocolos
    "No existen protocolos": 0,
    "Protocolos informales (solo veteranos saben cómo)": 2,
    "Documentados pero no se siguen ni auditan": 3,
    "Protocolos documentados + formación + autoevaluación periódica": 5,
    # P6 - Comunicación
    "Sin sistema formal: reuniones improvisadas, o sin reuniones": 0,
    "WhatsApp/email caótico sin estructura": 0,
    "Reuniones periódicas fijas pero sin herramienta digital": 2,
    "Sistema digital integrado (CRM, ERP, intranet) + protocolos de comunicación": 5,
    # P7 - KPIs ejecución
    "No medimos nada": 0,
    "Medimos ocasionalmente sin sistema": 2,
    "Check-lists existen pero sin seguimiento de datos": 3,
    "Timing medido + check-lists diarios + revisión semanal": 5,
    # P8 - Objetivos/incentivos
    "Sin estructura ni sistema de incentivos": 0,
    "Estructura básica pero sin vinculación a resultados ni incentivos": 2,
    "Sistema de estructuración existe + incentivos esporádicos sin métrica clara": 3,
    "Procesos estructurados + KPIs definidos + sistema de bonus/comisiones vinculado a logros": 5,
    # Opción común — actividades que no aplican
    "No aplica a mi actividad": 3,
    # P9 - Costes directos
    "No lo sé / No lo calculo": 0,
    "Lo calculo ocasionalmente, está por encima del 45%": 2,
    "Entre 35% y 45%": 3,
    "Por debajo del 35% con histórico mensual": 5,
    # P10 - Pedidos
    "WhatsApp, llamadas, caótico, sin autorización": 0,
    "Excel o papel, sin consolidación": 2,
    "App o sistema digital pero sin aprobación centralizada": 3,
    "Sistema digital + autorización + consolidación periódica": 5,
    # P11 - Desperdicios
    "No existe control": 0,
    "Control informal, estimado a ojo": 2,
    "Registro básico pero sin análisis": 3,
    "Control estricto + análisis de eficiencia + mejora continua": 5,
    # P12 - Almacén
    "Desorganizado, sin sistema, recepciones sin verificar": 0,
    "Ordenado pero sin sistema formal": 2,
    "Sistema básico + recepciones con control": 3,
    "Zonificación + control estricto + inventario perpetuo": 5,
    # P13 - Cliente ideal
    "No tengo definido el perfil de cliente": 0,
    "Idea aproximada pero sin datos": 2,
    "Perfil definido pero basado solo en intuición": 3,
    "Buyer persona documentado + validado con datos reales + actualizado": 5,
    # P14 - Fidelización
    "No mido repetición ni tengo programa": 0,
    "Sé que repiten pero no cuantificado, sin programa activo": 2,
    "Tasa medida + programa básico (tarjeta puntos, descuento)": 3,
    "Sistema CRM + segmentación + programa Ambassador + NPS >50": 5,
    # P15 - Diversificación
    "Más del 70% de un único perfil de cliente": 0,
    "50-70% de cliente principal, otros minoritarios": 2,
    "Diversificación clara pero sin estrategia activa de captación": 3,
    "Estrategia de diversificación activa + segmentación + canales alternativos": 5,
    # P16 - Reputación
    "No respondo reseñas ni hago encuestas": 0,
    "Respondo ocasionalmente, encuestas informales": 2,
    "Gestión activa de reseñas + encuestas básicas": 3,
    "Sistema de encuestas NPS + análisis de opiniones + respuesta protocolizada": 5,
    # P17 - Inventario equipos
    "No sé cuántos equipos tengo ni su estado": 0,
    "Lista básica sin fichas ni historial": 2,
    "Inventario parcial con algunas fichas": 3,
    "Inventario 100% + ficha técnica por equipo + historial de intervenciones": 5,
    # P18 - Mantenimiento preventivo
    "Solo reactivo (cuando se rompe, arreglamos)": 0,
    "Algunas revisiones puntuales sin plan anual": 2,
    "Mayoría al día pero sin sistema de alertas": 3,
    "100% cumplimiento + auditorías programadas + alertas preventivas": 5,
    # P19 - Averías
    "WhatsApp / llamadas al técnico de confianza": 0,
    "Excel o papel, sin priorización": 2,
    "Sistema básico de tickets pero sin seguimiento": 3,
    "Sistema de incidencias clasificado (A/B/C) + protocolo emergencias + técnicos visibles": 5,
    # P21 - Reporting
    "Solo cierres anuales con asesoría": 0,
    "Mensual básico (ingresos/gastos generales)": 2,
    "Semanal pero desestructurado o incompleto": 3,
    "Reporting semanal estructurado + mensual + alertas automáticas": 5,
    # P22 - KPIs financieros
    "Solo sé el total, no desgloso": 0,
    "Desglose básico pero sin asignación de costes reales": 2,
    "Análisis parcial con algunos costes asignados": 3,
    "Rentabilidad por línea + costes directos/indirectos asignados + comparativa histórica": 5,
    # P23 - Decisiones
    "100% intuición / experiencia": 0,
    "Mix: datos básicos + intuición mayoritaria": 2,
    "Datos relevantes pero sin dashboard ni sistema": 3,
    "Dashboard vivo + KPIs claros + decisiones documentadas con base numérica": 5,
    # P24 - Cash flow
    "No calculo break-even ni proyecciones": 0,
    "Break-even aproximado anual": 2,
    "Break-even por temporada + proyección básica": 3,
    "Cash-flow 3-6 meses + escenarios (optimista/pesimista) + alertas de desviación": 5,
}

AREAS = [
    ("RRHH y Organizacion",    ["p1",  "p2",  "p3",  "p4"],  "👥"),
    ("Operaciones y Procesos", ["p5",  "p6",  "p7",  "p8"],  "⚙️"),
    ("Compras y Costes",       ["p9",  "p10", "p11", "p12"], "📦"),
    ("Perfil de Cliente",      ["p13", "p14", "p15", "p16"], "🎯"),
    ("Mantenimiento",          ["p17", "p18", "p19", "p20"], "🔧"),
    ("Economia y Finanzas",    ["p21", "p22", "p23", "p24"], "💰"),
]

SCORE_RANGES = [
    (0,  21,  "Barco en llamas",  "Naufragio inminente — accion urgente necesaria",          "#dc2626"),
    (21, 41,  "Averias graves",   "Riesgo alto — necesitas refuerzos estructurales",          "#f97316"),
    (41, 61,  "Viento en contra", "En desarrollo — rumbo correcto pero con obstaculos",       "#d97706"),
    (61, 81,  "Buen marinero",    "Buen nivel — navegacion solida, margen de mejora",         "#16a34a"),
    (81, 101, "Capitan experto",  "Excelencia operativa — estas marcando el camino",          "#0284c7"),
]

AREA_MESSAGES = {
    "RRHH y Organizacion": {
        "bajo":  "Tu estructura de equipo necesita definicion urgente. Sin organigrama ni formacion estructurada, el negocio depende de personas clave con riesgo de colapso si alguna falla.",
        "medio": "Tienes bases de organizacion pero sin sistematizacion. El siguiente paso es documentar procesos y crear planes de formacion reales.",
        "alto":  "Buena estructura de equipo. Focaliza en la retencion del talento y en vincular objetivos individuales a los resultados del negocio.",
    },
    "Operaciones y Procesos": {
        "bajo":  "Operas de forma reactiva. Sin protocolos ni KPIs, cada dia es una improvisacion que cuesta dinero y energia.",
        "medio": "Tienes procesos pero no medicion sistematica. Implementar KPIs semanales y revisiones de equipo puede transformar tu operativa rapidamente.",
        "alto":  "Operaciones bien estructuradas. La clave ahora es vincular los KPIs a incentivos reales para maximizar el compromiso del equipo.",
    },
    "Compras y Costes": {
        "bajo":  "Sin control de costes directos ni gestion de stock, estas perdiendo margen sin saberlo. Esta area suele ser la de mayor impacto rapido en rentabilidad.",
        "medio": "Tienes cierto control pero sin sistematizacion. Implementar escandallos y pedidos estructurados puede mejorar tu margen un 3-5% en semanas.",
        "alto":  "Excelente control de costes. Enfocate ahora en la negociacion de condiciones marco con proveedores clave.",
    },
    "Perfil de Cliente": {
        "bajo":  "No conocer a tu cliente es operar a ciegas. Definir tu buyer persona y medir la repeticion es el primer paso para crecer de forma sostenible.",
        "medio": "Tienes intuicion sobre tu cliente pero sin datos que la validen. Un programa basico de fidelizacion y NPS puede darte informacion valiosa con poco esfuerzo.",
        "alto":  "Conoces bien a tu cliente. El siguiente nivel es segmentar activamente y adaptar tu oferta a cada perfil.",
    },
    "Mantenimiento": {
        "bajo":  "El mantenimiento reactivo es el mas caro. Una averia en un momento critico puede costarte mas que un plan preventivo anual completo.",
        "medio": "Tienes inventario pero sin plan preventivo real. Establecer un calendario de 52 semanas con responsables asignados es el cambio mas rentable que puedes hacer.",
        "alto":  "Buen nivel de mantenimiento preventivo. Incorpora el historial de vida util de equipos criticos para anticipar renovaciones.",
    },
    "Economia y Finanzas": {
        "bajo":  "Sin reporting ni control de cash-flow, las decisiones se toman a ciegas. Esta es la base de cualquier empresa que quiera crecer de forma sostenible.",
        "medio": "Tienes numeros pero no los usas como herramienta de decision. Un dashboard mensual sencillo puede cambiar por completo tu capacidad de reaccion.",
        "alto":  "Buena base financiera. El siguiente paso es la prevision a 3 meses y la creacion de escenarios para anticipar tensiones de tesoreria.",
    },
}


# ── Calculo de scores ──────────────────────────────────────────────────────────

def get_score(answer: str) -> int:
    return ANSWER_SCORES.get((answer or "").strip(), 0)


def get_area_message(area_name: str, score: int) -> str:
    msgs = AREA_MESSAGES.get(area_name, {})
    if score < 41:
        return msgs.get("bajo", "")
    if score < 71:
        return msgs.get("medio", "")
    return msgs.get("alto", "")


def calculate_results(data: dict) -> dict:
    area_results = []
    total_raw = 0

    for area_name, questions, icon in AREAS:
        raw = sum(get_score(data.get(q, "")) for q in questions)
        score = round((raw / 20) * 100)
        area_results.append({
            "name": area_name,
            "icon": icon,
            "score": score,
            "message": get_area_message(area_name, score),
        })
        total_raw += raw

    global_score = round((total_raw / 120) * 100)

    label, description, color = "—", "—", "#6b7280"
    for low, high, lbl, desc, clr in SCORE_RANGES:
        if low <= global_score < high:
            label, description, color = lbl, desc, clr
            break

    return {
        "global_score": global_score,
        "label": label,
        "description": description,
        "color": color,
        "areas": area_results,
    }


# ── Generacion del email HTML ──────────────────────────────────────────────────

def area_color(score: int) -> str:
    if score < 21: return "#fca5a5"
    if score < 41: return "#fed7aa"
    if score < 61: return "#fde68a"
    if score < 81: return "#bbf7d0"
    return "#bae6fd"


def score_bar(score: int, color: str) -> str:
    pct = max(score, 3)
    return (
        f'<div style="background:#3a5a45;border-radius:4px;height:10px;width:100%;">'
        f'<div style="background:{color};width:{pct}%;height:10px;border-radius:4px;"></div>'
        f'</div>'
    )



def _load_logo_tag() -> str:
    logo_path = os.path.join(os.path.dirname(__file__), "..", "public", "logo.png")
    try:
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="MB2 Management Teams" width="200" style="display:block;margin:0 auto;">'
    except Exception:
        return '<p style="color:#b87333;font-size:20px;font-family:Montserrat,Arial,sans-serif;font-weight:700;margin:0;">MB² Management Teams</p>'

LOGO_TAG = _load_logo_tag()


def build_html_email(nombre: str, results: dict) -> str:
    global_score = results["global_score"]
    label        = results["label"]
    description  = results["description"]
    color        = results["color"]
    areas        = results["areas"]
    fecha        = datetime.now().strftime("%d/%m/%Y")

    # Fila por area
    areas_rows = ""
    for a in areas:
        ac    = area_color(a["score"])
        bar   = score_bar(a["score"], ac)
        label_color = "#dc2626" if a["score"] < 41 else ("#d97706" if a["score"] < 61 else "#16a34a")
        areas_rows += f"""
        <tr>
          <td style="padding:14px 20px;border-bottom:1px solid #eef2ee;vertical-align:top;">
            <span style="font-size:20px;">{a["icon"]}</span>
            <strong style="margin-left:8px;color:#1e3a2f;font-size:14px;font-family:Montserrat,Arial,sans-serif;">{a["name"]}</strong>
            <p style="color:#5a7060;font-size:12px;margin:6px 0 0;line-height:1.5;">{a["message"]}</p>
          </td>
          <td style="padding:14px 20px;border-bottom:1px solid #eef2ee;width:140px;vertical-align:middle;">
            {bar}
          </td>
          <td style="padding:14px 20px;border-bottom:1px solid #eef2ee;text-align:right;vertical-align:middle;">
            <strong style="color:{label_color};font-size:20px;">{a["score"]}</strong>
            <span style="color:#8a8680;font-size:12px;">/100</span>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Tu Pre-Diagnostico MB2 Management Teams</title>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#e8e4dc;font-family:Inter,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#e8e4dc;">
<tr><td align="center" style="padding:32px 16px;">

  <table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(30,58,47,0.14);">

    <!-- CABECERA -->
    <tr>
      <td style="background:#1e3a2f;padding:36px 40px;text-align:center;">
        {LOGO_TAG}
        <div style="background:#2e8b57;height:1px;width:60px;margin:20px auto;opacity:0.5;"></div>
        <p style="color:#e8e4dc;font-size:16px;margin:0;letter-spacing:2px;font-family:Montserrat,Arial,sans-serif;font-weight:500;">Pre-Diagnostico Empresarial</p>
        <p style="color:#7a9a7e;font-size:12px;margin:8px 0 0;">{fecha}</p>
      </td>
    </tr>

    <!-- SALUDO -->
    <tr>
      <td style="padding:36px 40px 0;">
        <p style="color:#2d2d2d;font-size:16px;line-height:1.7;margin:0;">
          Hola <strong style="color:#1e3a2f;">{nombre}</strong>,
        </p>
        <p style="color:#4a5a4e;font-size:15px;line-height:1.8;margin:14px 0 0;">
          Acabas de dar el primer paso hacia una empresa mas solida. Aqui tienes el resultado de tu diagnostico en las <strong>6 areas clave</strong> del negocio. Estos numeros son tu punto de partida — y el comienzo de la transformacion.
        </p>
      </td>
    </tr>

    <!-- SCORE GLOBAL -->
    <tr>
      <td style="padding:32px 40px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#1e3a2f;border-radius:12px;">
          <tr>
            <td style="padding:32px;text-align:center;">
              <p style="color:#7a9a7e;font-size:11px;letter-spacing:4px;text-transform:uppercase;margin:0 0 10px;font-family:Montserrat,Arial,sans-serif;">Score Global MB²</p>
              <p style="color:{color};font-size:80px;font-weight:700;margin:0;line-height:1;font-family:Montserrat,Arial,sans-serif;">{global_score}</p>
              <p style="color:#e8e4dc;font-size:13px;margin:2px 0 0;">/100</p>
              <div style="background:#b87333;height:1px;width:40px;margin:16px auto;"></div>
              <p style="color:#b87333;font-size:20px;margin:0;font-style:italic;font-family:Montserrat,Arial,sans-serif;">"{label}"</p>
              <p style="color:#7a9a7e;font-size:13px;margin:8px 0 20px;">{description}</p>
              <div style="width:80%;margin:0 auto;">{score_bar(global_score, color)}</div>
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- INTERPRETACION RANGOS -->
    <tr>
      <td style="padding:0 40px 28px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <tr>
            <td style="font-size:11px;color:#6b7280;padding:4px 8px;border-left:3px solid #fca5a5;">0-20: Barco en llamas</td>
            <td style="font-size:11px;color:#6b7280;padding:4px 8px;border-left:3px solid #fed7aa;">21-40: Averias graves</td>
            <td style="font-size:11px;color:#6b7280;padding:4px 8px;border-left:3px solid #fde68a;">41-60: Viento en contra</td>
            <td style="font-size:11px;color:#6b7280;padding:4px 8px;border-left:3px solid #bbf7d0;">61-80: Buen marinero</td>
            <td style="font-size:11px;color:#6b7280;padding:4px 8px;border-left:3px solid #7a9a7e;">81+: Capitan experto</td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- DESGLOSE POR AREAS -->
    <tr>
      <td style="padding:0 40px 32px;">
        <h3 style="color:#1e3a2f;font-size:12px;letter-spacing:3px;text-transform:uppercase;margin:0 0 16px;padding-bottom:10px;border-bottom:2px solid #b87333;font-family:Montserrat,Arial,sans-serif;">
          Diagnostico por Areas
        </h3>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:10px;overflow:hidden;border:1px solid #dde8de;">
          {areas_rows}
        </table>
      </td>
    </tr>

    <!-- CTA CALENDLY -->
    <tr>
      <td style="padding:0 40px 40px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#1e3a2f;border-radius:12px;">
          <tr>
            <td style="padding:36px;text-align:center;">
              <p style="color:#b87333;font-size:11px;letter-spacing:4px;text-transform:uppercase;margin:0 0 12px;font-family:Montserrat,Arial,sans-serif;">Siguiente Paso</p>
              <p style="color:#ffffff;font-size:16px;line-height:1.7;margin:0 0 8px;">
                Este diagnostico es el inicio. El <strong>plan de accion personalizado</strong> es donde ocurre la transformacion real.
              </p>
              <p style="color:#7a9a7e;font-size:14px;margin:0 0 28px;line-height:1.6;">
                Agenda tu sesion estrategica gratuita de 30 minutos y descubramos juntos las palancas de mayor impacto para tu negocio.
              </p>
              <a href="{CALENDLY_URL}"
                 style="display:inline-block;background:#b87333;color:#ffffff;text-decoration:none;font-weight:700;font-size:15px;padding:16px 36px;border-radius:8px;letter-spacing:1px;font-family:Montserrat,Arial,sans-serif;">
                AGENDA TU SESION GRATUITA →
              </a>
              <p style="color:#5a7060;font-size:12px;margin:16px 0 0;">
                30 minutos · Sin compromiso · 100% gratuito
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- PRUEBA SOCIAL -->
    <tr>
      <td style="padding:0 40px 32px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7f4;border-left:4px solid #2e8b57;border-radius:0 8px 8px 0;">
          <tr>
            <td style="padding:20px 24px;">
              <p style="color:#2e8b57;font-size:11px;letter-spacing:3px;text-transform:uppercase;margin:0 0 8px;font-family:Montserrat,Arial,sans-serif;">Por que MB² Management Teams</p>
              <p style="color:#1e3a2f;font-size:14px;line-height:1.7;margin:0;">
                MB² ha acompanado a <strong>mas de 50 empresas</strong> en su proceso de estructuracion y crecimiento.
                Nuestros clientes experimentan mejoras medibles en eficiencia y rentabilidad en los primeros <strong>90 dias</strong>.
                No vendemos teoria — implantamos soluciones que funcionan en la realidad de tu negocio.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- FOOTER -->
    <tr>
      <td style="background:#1e3a2f;padding:20px 40px;text-align:center;">
        <p style="color:#7a9a7e;font-size:12px;margin:0;line-height:1.6;">
          © 2025 MB² Management Teams ·
          <a href="https://mb2team.com" style="color:#7a9a7e;text-decoration:none;">mb2team.com</a>
          · cuestionarios@mb2team.com
        </p>
        <p style="color:#3a5a45;font-size:11px;margin:6px 0 0;">
          Has recibido este informe porque completaste el diagnostico MB² en mb2team.com
        </p>
      </td>
    </tr>

  </table>
</td></tr>
</table>
</body>
</html>"""


# ── Envio de email ─────────────────────────────────────────────────────────────

def send_via_resend(to_email: str, subject: str, html_body: str) -> None:
    api_key = os.environ["RESEND_API_KEY"]
    payload = json.dumps({
        "from": "MB2 Diagnostico <cuestionarios@mb2team.com>",
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=9) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"Resend error {resp.status}")


def send_via_smtp(to_email: str, subject: str, html_body: str) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.hostinger.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ.get("SMTP_USER", "cuestionarios@mb2team.com")
    pwd  = os.environ["SMTP_PASS"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"MB2 Diagnostico <{user}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=ctx, timeout=8) as s:
        s.login(user, pwd)
        s.sendmail(user, to_email, msg.as_string())


def send_email(to_email: str, subject: str, html_body: str) -> None:
    if os.environ.get("RESEND_API_KEY"):
        send_via_resend(to_email, subject, html_body)
    else:
        send_via_smtp(to_email, subject, html_body)


# ── Mapeo campos Tally → API ───────────────────────────────────────────────────

TALLY_FIELD_MAP = {
    "Nombre completo":  "nombre",
    "Email profesional": "email",
    "¿Tienes un organigrama funcional actualizado con jefes de equipo definidos?": "p1",
    "¿Cuál es tu tasa de rotación anual aproximada?": "p2",
    "¿Tienes un plan de formación anual estructurado por puestos?": "p3",
    "¿Cómo gestionas los horarios y la cobertura de días libres/festivos?": "p4",
    "¿Tienes protocolos estándar de operación documentados (procesos, pasos, calidad)?": "p5",
    "¿Cómo se comunican los departamentos o áreas durante la operativa diaria?": "p6",
    "¿Mides tiempos de ejecución y tienes check-list de calidad?": "p7",
    "¿Existe un sistema que estructure los servicios/procesos y remunere los logros alcanzados?": "p8",
    "¿Conoces tu ratio de costes directos de adquisición sobre ingresos?": "p9",
    "¿Cómo gestionas los pedidos a proveedores o adquisiciones?": "p10",
    "¿Tienes control de desperdicio, mermas o eficiencia en tus procesos de adquisición/producción?": "p11",
    "¿Cómo gestionas tu almacén, stock o archivos de recepción?": "p12",
    "¿Conoces con precisión quién es tu cliente ideal (edad, origen, motivación, gasto)?": "p13",
    "¿Mides la tasa de clientes repetidores y tienes programa de fidelización?": "p14",
    "¿Tienes diversificación de perfiles de clientes o dependes de un único tipo?": "p15",
    "¿Gestionas activamente tu reputación online y encuestas de satisfacción?": "p16",
    "¿Tienes inventario completo de instalaciones y equipos con fichas técnicas?": "p17",
    "¿Tienes plan de mantenimiento preventivo anual programado?": "p18",
    "¿Cómo gestionas las averías y emergencias técnicas?": "p19",
    "¿Con qué frecuencia generas información económica?": "p21",
    "¿Analizas rentabilidad por línea de negocio o servicio?": "p22",
    "¿Tienes proyección de cash-flow y punto de equilibrio por temporada/período?": "p24",
    "¿Tus decisiones estratégicas se basan en datos o en intuición?": "p23",
}


def parse_tally_payload(raw: dict) -> dict:
    fields = raw.get("data", {}).get("fields", [])
    result = {}
    for field in fields:
        label = (field.get("label") or "").strip()
        value = field.get("value")
        options = {opt["id"]: opt["text"] for opt in field.get("options", []) if "id" in opt}
        if isinstance(value, list):
            texts = []
            for v in value:
                if isinstance(v, str) and v in options:
                    texts.append(options[v])
                elif isinstance(v, dict):
                    texts.append(v.get("text", ""))
                else:
                    texts.append(str(v))
            value = texts[0] if texts else ""
        api_key = TALLY_FIELD_MAP.get(label)
        if api_key and value is not None:
            result[api_key] = str(value)
    return result


# ── Handler Vercel ─────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            data   = json.loads(raw)

            # Detectar formato webhook de Tally
            if "data" in data and "fields" in data.get("data", {}):
                data = parse_tally_payload(data)

            nombre = (data.get("nombre") or data.get("name") or "").strip()
            email  = (data.get("email") or "").strip()

            if not email:
                return self._respond(400, {"error": "Campo 'email' requerido"})

            results = calculate_results(data)
            html    = build_html_email(nombre or "cliente", results)
            subject = f"Tu Pre-Diagnostico MB2 — Score {results['global_score']}/100"

            send_email(email, subject, html)

            self._respond(200, {
                "ok":           True,
                "score":        results["global_score"],
                "nivel":        results["label"],
                "email_enviado": email,
            })

        except Exception as exc:
            import traceback
            print(f"WEBHOOK ERROR: {exc}")
            print(traceback.format_exc())
            self._respond(500, {"error": str(exc)})

    def do_GET(self):
        self._respond(200, {"status": "MB2 Diagnostic API v1 — OK"})

    def _respond(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
