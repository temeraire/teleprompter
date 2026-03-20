# Teleprompter — Streamlit Web App

## Summary
Convert the PyQt6 desktop teleprompter to a Streamlit web app hosted at `tools.gregkiddfornevada.com/teleprompter`. The candidate uploads or pastes a script, and it scrolls white-on-black in the browser. Controls for speed, font size, play/pause. Sits behind the existing auth gateway.

## Tasks

- [x] **1. Create the Streamlit app (`streamlit_app.py`)**
  - Text input: file upload (.txt) or paste into a text area
  - Sidebar controls: play/pause, speed, font size
  - Teleprompter display via `st.components.v1.html()` with embedded HTML/CSS/JS for smooth scrolling
  - White text on black, large font, clean look

- [x] **2. Test locally**
  - `streamlit run streamlit_app.py`
  - Verify file upload, paste, scrolling, speed/font controls, pause/resume

- [x] **3. Add deployment files**
  - `requirements.txt` with streamlit
  - Nginx location block config for `/teleprompter`
  - Systemd service file for Streamlit (port 3003)

- [x] **4. Update portal page**
  - Add a fourth card to the tools portal HTML for Teleprompter

- [x] **5. Deploy to droplet**
  - Push code, set up on droplet, test behind auth

## Review

### Changes made
- **`streamlit_app.py`** — New Streamlit app. Sidebar has file upload (.txt), paste text area, speed slider (0.5–5.0), and font size slider (24–96px). Main area renders a full HTML/CSS/JS teleprompter component via `st.components.v1.html()`. White text on black, smooth `requestAnimationFrame` scrolling, click or spacebar to start/pause.
- **`requirements.txt`** — Just `streamlit`.
- **`deploy/teleprompter.conf`** — Nginx location block for `/teleprompter` and `/_stcore` (Streamlit WebSocket), proxying to port 3003.
- **`deploy/teleprompter.service`** — Systemd unit running Streamlit headless on port 3003 with `--server.baseUrlPath /teleprompter`.
- **`AuthGateway/portal.html`** — Added 4th tool card linking to `/teleprompter`.
