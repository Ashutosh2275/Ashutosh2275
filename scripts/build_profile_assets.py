"""Generates the animated profile SVGs into assets/. Run: python scripts/build_profile_assets.py"""
import os, random, xml.etree.ElementTree as ET
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT + "/projects", exist_ok=True)
F = "font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,Roboto,Helvetica,Arial,sans-serif"
M = "font-family:'SF Mono',Consolas,'Courier New',monospace"
DEFS = """<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#F1F4FF"/></linearGradient>
<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3B82F6"/><stop offset=".55" stop-color="#6366F1"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient>
<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#6366F1" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<radialGradient id="o1"><stop offset="0" stop-color="#6366F1" stop-opacity=".20"/><stop offset="1" stop-color="#6366F1" stop-opacity="0"/></radialGradient>
<radialGradient id="o2"><stop offset="0" stop-color="#3B82F6" stop-opacity=".18"/><stop offset="1" stop-color="#3B82F6" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>"""

def svg(w, h, body):
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{DEFS}{body}</svg>'
    ET.fromstring(s)
    return s

def save(name, s):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(s)

def chipw(t, fs=11):
    return int(len(t) * fs * 0.6 + 20)

def chips(items, x0, y0, maxw, fs=11, h=24, gap=8, fill="#EEF2FF", stroke="#E2E8F7", tc="#334155"):
    x, y, out = 0, 0, []
    for t in items:
        w = chipw(t, fs)
        if x + w > maxw:
            x, y = 0, y + h + gap
        out.append(f'<g transform="translate({x0+x},{y0+y})"><rect width="{w}" height="{h}" rx="{h/2}" fill="{fill}" stroke="{stroke}"/>'
                   f'<text x="{w/2}" y="{h/2+4}" text-anchor="middle" style="{F};font-size:{fs}px;font-weight:600" fill="{tc}">{t}</text></g>')
        x += w + gap
    return "".join(out), y + h

# ---------------- BANNER ----------------
def banner():
    random.seed(7)
    parts = ['<rect width="1000" height="340" rx="22" fill="url(#bg)"/>',
             '<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#6366F1" stroke-opacity=".10"/>'
             '<animateTransform attributeName="patternTransform" type="translate" from="0 0" to="40 40" dur="6s" repeatCount="indefinite"/></pattern>',
             '<rect width="1000" height="340" rx="22" fill="url(#grid)"/>',
             '<circle cx="180" cy="60" r="230" fill="url(#o1)"><animate attributeName="cx" values="180;320;180" dur="14s" repeatCount="indefinite"/><animate attributeName="cy" values="60;120;60" dur="11s" repeatCount="indefinite"/></circle>',
             '<circle cx="820" cy="290" r="240" fill="url(#o2)"><animate attributeName="cx" values="820;700;820" dur="12s" repeatCount="indefinite"/><animate attributeName="cy" values="290;230;290" dur="9s" repeatCount="indefinite"/></circle>']
    for i in range(34):
        x, y, r = random.randint(20, 980), random.randint(20, 320), random.choice([1, 1.4, 1.8, 2.2])
        d, b = random.uniform(4, 9), random.uniform(0, 6)
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#818CF8" opacity=".5"><animate attributeName="cy" values="{y};{y-28};{y}" dur="{d:.1f}s" begin="-{b:.1f}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".15;.9;.15" dur="{d:.1f}s" begin="-{b:.1f}s" repeatCount="indefinite"/></circle>')
    # orbital neural visual
    o = ['<g transform="translate(810,170)">']
    for r, dur, rev in [(62, 14, 1), (100, 22, -1), (138, 34, 1)]:
        o.append(f'<circle r="{r}" fill="none" stroke="#6366F1" stroke-opacity=".35" stroke-dasharray="3 7"/>')
        o.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0" to="{360*rev}" dur="{dur}s" repeatCount="indefinite"/>'
                 f'<circle cx="{r}" r="6" fill="#3B82F6" filter="url(#glow)"/><circle cx="{-r}" cy="0" r="4" fill="#8B5CF6" filter="url(#glow)"/></g>')
    o.append('<circle r="30" fill="#FFFFFF" stroke="url(#acc)" stroke-width="2" filter="url(#glow)"><animate attributeName="r" values="30;34;30" dur="3s" repeatCount="indefinite"/></circle>')
    o.append(f'<text y="7" text-anchor="middle" style="{F};font-size:20px;font-weight:800" fill="url(#acc)">AI</text></g>')
    parts += o
    parts.append('<rect y="-4" width="1000" height="3" fill="url(#shine)" opacity=".35"><animate attributeName="y" values="-4;340" dur="7s" repeatCount="indefinite"/></rect>')
    parts.append(f'<text x="64" y="86" style="{F};font-size:13px;font-weight:700;letter-spacing:6px" fill="#4F46E5">ASHUTOSH MISHRA</text>')
    parts.append(f'<text x="64" y="146" style="{F};font-size:46px;font-weight:800;letter-spacing:-1px" fill="#0F172A">AI/ML &amp; Full-Stack</text>')
    parts.append(f'<text x="64" y="200" style="{F};font-size:46px;font-weight:800;letter-spacing:-1px" fill="url(#acc)">Developer</text>')
    lines = ["Building intelligent, scalable software", "LLMs  /  RAG  /  Computer Vision", "FastAPI  /  React  /  PostgreSQL  /  Docker", "B.Tech CSE  /  ITER, SOA University  /  2027"]
    n, f = len(lines), 0.03
    for i, t in enumerate(lines):
        a, b = i / n, (i + 1) / n
        pts = ([(0, 1), (b - f, 1), (b, 0), (1, 0)] if i == 0 else
               [(0, 0), (a, 0), (a + f, 1), (1 - f, 1), (1, 0)] if i == n - 1 else
               [(0, 0), (a, 0), (a + f, 1), (b - f, 1), (b, 0), (1, 0)])
        kt, vv = ";".join(f"{p[0]:.3f}" for p in pts), ";".join(str(p[1]) for p in pts)
        parts.append(f'<text x="64" y="248" opacity="0" style="{M};font-size:16px" fill="#475569"><tspan fill="#3B82F6">&gt; </tspan>{t}'
                     f'<animate attributeName="opacity" values="{vv}" keyTimes="{kt}" dur="16s" repeatCount="indefinite"/></text>')
    parts.append(f'<text x="64" y="300" style="{F};font-size:12px;letter-spacing:1px" fill="#64748B">BHUBANESWAR, ODISHA  /  TURNING REAL-WORLD PROBLEMS INTO INTELLIGENT SOLUTIONS</text>')
    parts.append('<rect x="1" y="1" width="998" height="338" rx="22" fill="none" stroke="#E2E8F7"/>')
    save("banner.svg", svg(1000, 340, "".join(parts)))

# ---------------- SECTION HEADERS ----------------
def header(name, tag, title):
    b = (f'<circle cx="14" cy="26" r="5" fill="#3B82F6" filter="url(#glow)"><animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></circle>'
         f'<text x="32" y="22" style="{M};font-size:11px;letter-spacing:3px" fill="#6366F1">{tag}</text>'
         f'<text x="32" y="48" style="{F};font-size:26px;font-weight:800;letter-spacing:-.4px" fill="#0F172A">{title}</text>'
         '<rect x="0" y="60" width="960" height="2" rx="1" fill="#334155" opacity=".5"/>'
         '<rect x="0" y="59" width="160" height="4" rx="2" fill="url(#acc)"><animate attributeName="x" values="-160;960" dur="4.5s" repeatCount="indefinite"/></rect>')
    save(f"header-{name}.svg", svg(960, 68, b))

# ---------------- JOURNEY (education / experience / focus) ----------------
def journey():
    tiles = [("EDUCATION", "B.Tech, Computer Science", "ITER, SOA University", "Bhubaneswar  /  Class of 2027"),
             ("EXPERIENCE", "DeepSurge", "Odisha Computer Application Centre", "OCAC  /  technical experience"),
             ("FOCUS", "AI/ML  /  GenAI  /  Backend", "Full-stack product engineering", "RAG  /  Computer Vision  /  Automation")]
    p = []
    for i, (k, t1, t2, t3) in enumerate(tiles):
        x = i * 328
        p.append(f'<g transform="translate({x},0)"><rect width="304" height="140" rx="16" fill="url(#bg)" stroke="#E2E8F7"/>'
                 f'<rect width="304" height="140" rx="16" fill="none" stroke="url(#acc)" stroke-width="1.6" stroke-dasharray="90 700"><animate attributeName="stroke-dashoffset" from="790" to="0" dur="{6+i}s" repeatCount="indefinite"/></rect>'
                 f'<circle cx="26" cy="30" r="4" fill="#3B82F6" filter="url(#glow)"><animate attributeName="opacity" values="1;.25;1" dur="{2+i*.5}s" repeatCount="indefinite"/></circle>'
                 f'<text x="42" y="34" style="{M};font-size:11px;letter-spacing:3px" fill="#4F46E5">{k}</text>'
                 f'<text x="24" y="72" style="{F};font-size:18px;font-weight:800" fill="#0F172A">{t1}</text>'
                 f'<text x="24" y="98" style="{F};font-size:13px" fill="#475569">{t2}</text>'
                 f'<text x="24" y="120" style="{F};font-size:12px" fill="#64748B">{t3}</text></g>')
    save("journey.svg", svg(960, 140, "".join(p)))

# ---------------- PROJECT CARDS ----------------
def icon(kind):
    g = ['<g transform="translate(24,24)"><rect width="84" height="84" rx="14" fill="#FFFFFF" stroke="#E2E8F7"/>']
    if kind == "qr":
        random.seed(3)
        for r in range(5):
            for c in range(5):
                d = random.uniform(1.6, 4); b = random.uniform(0, 3)
                g.append(f'<rect x="{14+c*12}" y="{14+r*12}" width="9" height="9" rx="2" fill="#3B82F6"><animate attributeName="opacity" values=".15;1;.15" dur="{d:.1f}s" begin="-{b:.1f}s" repeatCount="indefinite"/></rect>')
    elif kind == "ecg":
        g.append('<path d="M8 44H26L33 22L45 68L54 32L60 44H76" fill="none" stroke="#C7D2FE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
                 '<path d="M8 44H26L33 22L45 68L54 32L60 44H76" pathLength="100" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="30 70" filter="url(#glow)">'
                 '<animate attributeName="stroke-dashoffset" from="30" to="-70" dur="2.2s" repeatCount="indefinite"/></path>')
    elif kind == "det":
        g.append('<g fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round"><path d="M20 30V20H30M54 20H64V30M64 54V64H54M30 64H20V54"/></g>'
                 '<circle cx="42" cy="38" r="7" fill="#6366F1"/><path d="M29 58C29 48 55 48 55 58" fill="#6366F1"/>'
                 '<rect x="14" y="40" width="56" height="2" fill="#3B82F6" opacity=".8" filter="url(#glow)"><animate attributeName="y" values="16;66;16" dur="2.8s" repeatCount="indefinite"/></rect>')
    else:
        for i, h in enumerate([20, 34, 28, 46, 58]):
            x = 14 + i * 13
            g.append(f'<rect x="{x}" y="{70-h}" width="9" height="{h}" rx="2" fill="#6366F1"><animate attributeName="height" values="{h};{h+10};{h}" dur="{2+i*.3:.1f}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="y" values="{70-h};{60-h};{70-h}" dur="{2+i*.3:.1f}s" repeatCount="indefinite"/></rect>')
        g.append('<path d="M12 56L30 44L46 48L72 18" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" filter="url(#glow)"/>')
    g.append("</g>")
    return "".join(g)

def project(fn, n, cat, title, d1, d2, tech, kind, repo):
    cx, cy = chips(tech, 24, 140, 422, fs=11, h=24)
    b = ('<rect width="470" height="250" rx="18" fill="url(#bg)" stroke="#E2E8F7"/>'
         '<rect x="1.5" y="1.5" width="467" height="247" rx="17" fill="none" stroke="url(#acc)" stroke-width="2" stroke-dasharray="170 1260"><animate attributeName="stroke-dashoffset" from="1430" to="0" dur="7s" repeatCount="indefinite"/></rect>'
         '<circle cx="440" cy="30" r="90" fill="url(#o1)"><animate attributeName="r" values="80;110;80" dur="6s" repeatCount="indefinite"/></circle>'
         + icon(kind) +
         f'<text x="126" y="44" style="{M};font-size:10px;letter-spacing:2px" fill="#3B82F6">{cat}</text>'
         f'<text x="126" y="72" style="{F};font-size:24px;font-weight:800" fill="#0F172A">{title}</text>'
         f'<text x="126" y="94" style="{F};font-size:12px" fill="#475569">{d1}</text>'
         f'<text x="126" y="111" style="{F};font-size:12px" fill="#475569">{d2}</text>'
         + cx +
         f'<text x="24" y="232" style="{M};font-size:11px" fill="#4F46E5">github.com/Ashutosh2275/{repo}  -&gt;</text>'
         f'<text x="446" y="232" text-anchor="end" style="{M};font-size:11px" fill="#475569">0{n}</text>')
    save(f"projects/{fn}.svg", svg(470, 250, b))

# ---------------- SKILLS ----------------
def skills():
    p = ['<clipPath id="clip"><rect width="960" height="108" rx="16"/></clipPath>', '<rect width="960" height="108" rx="16" fill="url(#bg)" stroke="#E2E8F7"/>', '<g clip-path="url(#clip)">']
    rows = [(["Python", "PyTorch", "TensorFlow", "LangChain", "RAG", "YOLOv8", "OpenCV", "Scikit-learn", "Hugging Face", "XGBoost", "Pandas", "NumPy"], 14, "-1"),
            (["React", "TypeScript", "FastAPI", "Node.js", "PostgreSQL", "MongoDB", "Redis", "Docker", "AWS", "Kotlin", "Electron", "Tailwind CSS"], 58, "1")]
    for words, y, dirn in rows:
        seq, x = [], 0
        for w_ in words:
            cw = int(len(w_) * 8.2 + 52) + 8
            seq.append(f'<g transform="translate({x},0)"><rect width="{cw-8}" height="34" rx="17" fill="#EEF2FF" stroke="#E2E8F7"/><circle cx="16" cy="17" r="3" fill="#3B82F6"/>'
                       f'<text x="27" y="22" style="{F};font-size:13px;font-weight:600" fill="#1E293B">{w_}</text></g>')
            x += cw + 6
        W = x
        a, b2 = (0, -W) if dirn == "-1" else (-W, 0)
        p.append(f'<g transform="translate(0,{y})"><g><animateTransform attributeName="transform" type="translate" from="{a} 0" to="{b2} 0" dur="38s" repeatCount="indefinite"/>'
                 f'{"".join(seq)}<g transform="translate({W},0)">{"".join(seq)}</g><g transform="translate({2*W},0)">{"".join(seq)}</g></g></g>')
    p.append('</g>')
    cats = [("LANGUAGES", ["Python", "Java", "C", "JavaScript", "TypeScript", "SQL"]),
            ("AI / ML + VISION", ["Machine Learning", "Deep Learning", "Computer Vision", "Predictive Analytics", "Time-Series", "Anomaly Detection"]),
            ("GENAI + LLM", ["LLMs", "RAG", "LangChain", "Hugging Face", "Prompt Engineering", "Google GenAI", "OCR"]),
            ("FRONTEND + APPS", ["React", "TypeScript", "Vite", "Tailwind CSS", "Zustand", "Kotlin", "Jetpack Compose", "Electron"]),
            ("BACKEND + APIS", ["FastAPI", "Flask", "Node.js", "Express", "Fastify", "REST APIs", "JWT Auth"]),
            ("DATA + CLOUD", ["PostgreSQL", "MongoDB", "MySQL", "Redis", "Firebase", "Supabase", "Docker", "AWS", "Nginx", "Linux"])]
    built = [chips(items, 18, 46, 264, fs=11, h=24) for _, items in cats]
    ch = max(b[1] for b in built) + 46 + 18
    for i, ((name, _), (cx, _)) in enumerate(zip(cats, built)):
        col, row = i % 3, i // 3
        x, y = col * 328, 132 + row * (ch + 20)
        p.append(f'<g transform="translate({x},{y})"><rect width="304" height="{ch}" rx="16" fill="url(#bg)" stroke="#E2E8F7"/>'
                 f'<rect x="18" y="0" width="60" height="3" rx="1.5" fill="url(#shine)"><animate attributeName="x" values="12;226;12" dur="{5+i}s" repeatCount="indefinite"/></rect>'
                 f'<circle cx="24" cy="26" r="4" fill="#6366F1" filter="url(#glow)"/><text x="40" y="30" style="{M};font-size:11px;letter-spacing:2.5px" fill="#4F46E5">{name}</text>{cx}</g>')
    H = 132 + 2 * ch + 20
    save("skills.svg", svg(960, H, "".join(p)))

# ---------------- FOOTER ----------------
def footer():
    def wave(amp, y, color, dur, op):
        d = f"M0 {y}"
        for k in range(0, 1440, 240):
            d += f" q60 {-amp} 120 0 t120 0"
        d += " V150 H0 Z"
        return f'<path d="{d}" fill="{color}" opacity="{op}"><animateTransform attributeName="transform" type="translate" from="0 0" to="-240 0" dur="{dur}s" repeatCount="indefinite"/></path>'
    b = ('<clipPath id="fc"><rect width="960" height="150" rx="18"/></clipPath><rect width="960" height="150" rx="18" fill="url(#bg)" stroke="#E2E8F7"/>'
         '<g clip-path="url(#fc)">' + wave(18, 112, "#3B82F6", 9, .12) + wave(14, 124, "#6366F1", 13, .18) + wave(10, 134, "#8B5CF6", 17, .22) + '</g>'
         f'<text x="480" y="62" text-anchor="middle" style="{F};font-size:46px;font-weight:800" fill="url(#acc)" opacity=".9">&#8220;</text>'
         f'<text x="480" y="92" text-anchor="middle" style="{F};font-size:20px;font-weight:600" fill="#1E293B">Using AI/ML to build impactful, deployable tech,</text>'
         f'<text x="480" y="118" text-anchor="middle" style="{F};font-size:20px;font-weight:600" fill="#1E293B">not just prototypes.</text>')
    save("footer.svg", svg(960, 150, b))

if __name__ == "__main__":
    banner(); journey(); skills(); footer()
    for k, t in [("about", "01  /  ABOUT"), ("activity", "02  /  ACTIVITY"), ("projects", "03  /  WORK"), ("skills", "04  /  STACK"), ("connect", "05  /  CONTACT")]:
        header(k, t, {"about": "About Me", "activity": "GitHub Activity", "projects": "Featured Projects", "skills": "Technical Skills", "connect": "Let's Connect"}[k])
    project("dinedeck", 1, "FULL-STACK  /  RESTAURANT TECH", "DineDeck", "Multi-platform restaurant ecosystem: QR ordering,", "POS, KDS and real-time kitchen operations.",
            ["Kotlin", "Compose", "React", "TypeScript", "Fastify", "PostgreSQL", "Redis", "Electron"], "qr", "Dinedeck")
    project("datacure", 2, "HEALTHCARE  /  AI-ML", "DataCure", "Hospital management with predictive analytics:", "readmission risk, no-shows and demand.",
            ["React", "Flask", "PostgreSQL", "Scikit-learn", "Redis", "Docker", "AWS"], "ecg", "Datacure")
    project("drai-ai", 3, "COMPUTER VISION  /  DEEP LEARNING", "DRAI-AI", "YOLOv8 detection of people, safety helmets", "and fire in images and live webcam feeds.",
            ["Python", "PyTorch", "YOLOv8", "Ultralytics", "OpenCV"], "det", "DRAI-AI")
    project("arthsavora", 4, "FINTECH  /  PERSONAL FINANCE", "ARTHSAVORA", "AI-powered finance app: expense tracking,", "budgeting, receipt OCR and insights.",
            ["FastAPI", "React", "MongoDB", "Scikit-learn", "Tesseract OCR", "Supabase", "JWT"], "bars", "ARTHSAVORA")
    print("assets generated")
