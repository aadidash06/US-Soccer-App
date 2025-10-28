====================Description & Technical Choices====================


===========What it does===========


A Streamlit app that loads SkillCorner tracking data (x/y for 22 players + ball at 10–30 FPS), lets you scrub frame-by-frame, select 0–10s windows, and export clips as GIF/MP4. It mirrors a video analyst’s clip/tag workflow while preserving off-ball context from raw positional data.



===========Why these choices===========


Language: Python 3.10+ — rich data/plotting ecosystem, fast prototyping.

UI: Streamlit for stateful widgets and rapid analyst-facing interfaces.

Pitch rendering: streamlit-soccer (primary) with Plotly fallback to ensure portability when the widget isn’t available.

Data loading: kloppy for standardized football data access (SkillCorner Open Data).

Imaging/encoding: Pillow + imageio (GIF everywhere), imageio-ffmpeg + ffmpeg (MP4).

Caching: On-disk cache under app/data_cache/ + Streamlit caching decorators to avoid re-downloads.

Project structure: Clear separation of concerns — loaders (I/O), transforms (normalization), render (encoding), main (UI/state).



===========How to Use===========


In the sidebar, enter a SkillCorner match ID (e.g., 2221637) and toggle “include empty frames” if desired.

Click Load tracking data (first load downloads; subsequent loads use cache).

Use the scrubber to browse frames on the pitch.

Set Mark In / Mark Out (max 10s).

Choose GIF or MP4, then Render clip. Download or (for GIF) preview inline.

Output naming: clip_<match_id>_<start>-<end>.<ext>


====================Tech Stack & Architecture====================


===========Tech Stack===========


Language: Python 3.10+

UI: Streamlit

Pitch Rendering: streamlit-soccer (primary), Plotly (fallback)

Data Access: kloppy (SkillCorner Open Data)

Imaging/Encoding: Pillow, imageio, imageio-ffmpeg (+ system ffmpeg for MP4)

Caching: Streamlit @st.cache_* + on-disk cache under app/data_cache/

External dependency

ffmpeg in PATH (only required for MP4; GIF works without it)



===========Project Structure===========


app/

  main.py          # Streamlit UI, sidebar, session state, user interactions
  
  loaders.py       # Download + cache SkillCorner datasets via 'kloppy'
  
  transforms.py    # Normalize Kloppy frames → renderable JSON payloads/metadata
  
  render.py        # Frames → GIF/MP4 via imageio(/ffmpeg)
  
  data_cache/      # On-disk cache: matches/<match_id>/...
  
requirements.txt   # Python dependencies



===========Data & Control Flow (High-Level)===========


User selects match_id

        │
        ▼
        
loaders.load_skillcorner_tracking(match_id)

  └─ fetch + cache JSONL/metadata under app/data_cache/matches/<id>/
  
        │
        ▼
        
transforms.frames_to_payloads(...)

  └─ normalized frame dicts for rendering/UI
  
        │
        ├─ Streamlit UI scrubber updates current frame(s) on pitch
        ▼
        
render.render_clip(start, end, format)

  └─ GIF (imageio) or MP4 (imageio-ffmpeg + ffmpeg), return/download


====================Link to Project====================

https://trackingclipbuilder.streamlit.app/
