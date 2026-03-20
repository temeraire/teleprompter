"""
Streamlit Teleprompter — white-on-black scrolling text in the browser.
Upload a .txt file or paste a script, then control speed and font size from the sidebar.
"""

import streamlit as st

st.set_page_config(page_title="Teleprompter", layout="wide")

# ── Sidebar controls ──────────────────────────────────────────────────────────

st.sidebar.title("Teleprompter")

uploaded_file = st.sidebar.file_uploader("Upload a script (.txt)", type=["txt"])
pasted_text = st.sidebar.text_area("Or paste your script here", height=150)

# Determine which text source to use
script_text = ""
if uploaded_file is not None:
    script_text = uploaded_file.read().decode("utf-8").strip()
elif pasted_text.strip():
    script_text = pasted_text.strip()

st.sidebar.markdown("---")
speed = st.sidebar.slider("Scroll speed", min_value=0.5, max_value=5.0, value=1.5, step=0.25)
font_size = st.sidebar.slider("Font size (px)", min_value=16, max_value=60, value=24, step=2)
strip_height = st.sidebar.slider("Strip height (px)", min_value=100, max_value=300, value=150, step=10)

# ── Main area ─────────────────────────────────────────────────────────────────

if not script_text:
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:center;
                    height:60vh;color:#888;font-size:20px;font-family:sans-serif;
                    flex-direction:column;gap:12px;">
            <div>Upload or paste a script in the sidebar, then click <b>Launch Teleprompter</b>.</div>
            <div style="font-size:14px;color:#666;">
                The teleprompter opens fullscreen with the text in a narrow strip
                at the very top of your screen — right under the camera.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    import json
    escaped_text = json.dumps(script_text)

    # The launch button sits inside an HTML component so it can call the
    # Fullscreen API and open the teleprompter in-place without browser chrome.
    teleprompter_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: transparent; font-family: sans-serif; }}

        /* ── Launch button (shown before fullscreen) ── */
        #launch-btn {{
            display: block;
            margin: 24px auto;
            padding: 14px 36px;
            font-size: 18px;
            font-weight: 600;
            color: #fff;
            background: #2a6a2a;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }}
        #launch-btn:hover {{ background: #3a8a3a; }}
        #instructions {{
            text-align: center;
            color: #888;
            font-size: 13px;
            margin-top: 8px;
        }}

        /* ── Fullscreen teleprompter ── */
        #teleprompter {{
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100vw;
            height: 100vh;
            background: #000;
            cursor: pointer;
            user-select: none;
            -webkit-user-select: none;
            z-index: 99999;
        }}
        /* Narrow scrolling strip at the very top */
        #strip {{
            position: absolute;
            top: 0; left: 50%;
            transform: translateX(-50%);
            width: 420px;
            height: {strip_height}px;
            overflow: hidden;
        }}
        #text {{
            position: absolute;
            top: {strip_height}px;
            left: 12px;
            right: 12px;
            color: #fff;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: {font_size}px;
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        #status {{
            position: fixed;
            bottom: 16px;
            right: 20px;
            color: #333;
            font-size: 14px;
            pointer-events: none;
            z-index: 100000;
        }}
        #start-overlay {{
            position: absolute;
            top: 0; left: 0;
            width: 100%;
            height: {strip_height}px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 22px;
            font-family: sans-serif;
            z-index: 100001;
            background: #000;
        }}
        /* Subtle border at bottom of strip so you can see the boundary */
        #strip-border {{
            position: absolute;
            top: {strip_height}px;
            left: 50%;
            transform: translateX(-50%);
            width: 420px;
            height: 1px;
            background: #222;
        }}
    </style>
    </head>
    <body>

    <button id="launch-btn">Launch Teleprompter</button>
    <div id="instructions">
        Opens fullscreen — text scrolls in a strip at the top of your screen, right under the camera.<br>
        Click or press Space to start / pause. Press Escape to exit.
    </div>

    <div id="teleprompter">
        <div id="strip">
            <div id="text"></div>
            <div id="start-overlay">Click to start</div>
        </div>
        <div id="strip-border"></div>
        <div id="status"></div>
    </div>

    <script>
        const launchBtn = document.getElementById('launch-btn');
        const teleprompter = document.getElementById('teleprompter');
        const textEl = document.getElementById('text');
        const statusEl = document.getElementById('status');
        const overlay = document.getElementById('start-overlay');
        const stripHeight = {strip_height};

        const scriptText = {escaped_text};
        textEl.textContent = scriptText;

        let scrollPos = 0;
        let scrolling = false;
        let started = false;
        const speed = {speed};
        let lastTime = null;

        function tick(timestamp) {{
            if (!lastTime) lastTime = timestamp;
            const delta = timestamp - lastTime;
            lastTime = timestamp;

            if (scrolling) {{
                scrollPos += speed * (delta / 33.0);
                const newTop = stripHeight - scrollPos;

                if (newTop + textEl.offsetHeight < 0) {{
                    scrollPos = 0;
                }}

                textEl.style.top = (stripHeight - scrollPos) + 'px';
            }}

            requestAnimationFrame(tick);
        }}

        launchBtn.addEventListener('click', function() {{
            teleprompter.style.display = 'block';
            // Request fullscreen on the teleprompter div
            const el = document.documentElement;
            if (el.requestFullscreen) el.requestFullscreen();
            else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
            requestAnimationFrame(tick);
        }});

        // Exit fullscreen → hide teleprompter and reset
        document.addEventListener('fullscreenchange', function() {{
            if (!document.fullscreenElement) {{
                teleprompter.style.display = 'none';
                scrolling = false;
                started = false;
                scrollPos = 0;
                textEl.style.top = stripHeight + 'px';
                overlay.style.display = 'flex';
                statusEl.textContent = '';
                lastTime = null;
            }}
        }});

        teleprompter.addEventListener('click', function() {{
            if (!started) {{
                started = true;
                overlay.style.display = 'none';
                scrolling = true;
                statusEl.textContent = 'Playing';
                return;
            }}
            scrolling = !scrolling;
            statusEl.textContent = scrolling ? 'Playing' : 'Paused';
        }});

        document.addEventListener('keydown', function(e) {{
            if (!teleprompter.style.display || teleprompter.style.display === 'none') return;
            if (e.code === 'Space') {{
                e.preventDefault();
                if (!started) {{
                    started = true;
                    overlay.style.display = 'none';
                    scrolling = true;
                    statusEl.textContent = 'Playing';
                    return;
                }}
                scrolling = !scrolling;
                statusEl.textContent = scrolling ? 'Playing' : 'Paused';
            }}
        }});
    </script>
    </body>
    </html>
    """

    st.components.v1.html(teleprompter_html, height=120, scrolling=False)
