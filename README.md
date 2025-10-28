============TASK============

At US Soccer, we're always looking for new ways to deliver metrics to our coaching staff, performance analysts, and talent identification department using the advanced datasets at our disposal. One of those datasets is "tracking data": raw x/y positions for all 22 players + the ball on the field during a match captured at 10-30 frames per second (FPS). This dataset allows us to capture key off-ball context during match events to better measure player impact on possession sequences and throughout games.

As part of this project, we're looking for a way to better visualize tracking data much like how our video analysts clip and tag video. Using one game of tracking data from the public dataset from SkillCorner, we'd like you to build a web application (built in any language/framework) that enables users to:

- Scrub through the tracking dataset using a slider (like a YouTube video – without the thumbnail preview)
- Clip arbitrary 0-10 second sequences of tracking data for other users to view
  o How users can view the clips is up to you: download as GIF, view as linked timestamp (like YouTube chapters), etc

Data To Use

You will select one game of tracking data from SkillCorner's opendata dataset:
https://github.com/SkillCorner/opendata

Documentation on the dataset itself is available at:
https://github.com/SkillCorner/opendata?tab=readme-ov-file#documentation

====================
DATA STRUCTURE AND COORDINATE SYSTEM
====================

Data Structure:
The data directory contains:
- matches.json file with basic information about the match. Using this file, pick the id of your match of interest.
- matches folder with one folder for each match (named with its id).
- aggregates folder with a csv for the season level, aggregated data for AUS midifielders in 2024/2025.

For each match, there are four files:
- {id}_match.json contains lineup information, time played, referee, pitch size...
- {id}_tracking_extrapolated.jsonl contains the tracking data (the players and the ball).
- {id}_dynamic_events.csv contains our Game Intelligence's dynamic events file (See further for specs.)
- {id}_phases_of_play.csv contains our Game Intelligence's PHASES OF PLAY framework file. (See further for specs.)

Tracking Data Description:
The tracking data is a list. Each element of the list is the result of the tracking for a frame, it's a dictionary with keys:
- frame: the frame of the video the data comes from at 10 fps.
- timestamp: the timestamp in the match time with a precision of 1/10s.
- period: 1 or 2.
- ball_data: the tracking data for the ball at this frame. Dictionary
- possession: dict with keys player_id and group which indicates which player/team (home or away team) are in possession
- image_corners_projection: coordinates of polygon of the detected area.
- player_data: list of information of the players at the given frame.

Each element of the player_data list is a player found at this frame. It's a dictionary with keys:
- x: x coordinate of the object
- y: y coordinate of the object
- player_id: identifier of the player
- is_detected: flag that mentions if the player is detected on the screen or extrapolated

COORDINATE SYSTEM:
For the spatial coordinates, the unit of the field modelization is the meter, the center of the coordinates is at the center of the pitch.

The x axis is the long side and the y axis in the short side.

Here is an illustration for a field of size 105mx68m:

Field Coordinate System (105m x 68m):
- Origin (0, 0) is at the CENTER of the pitch
- X-axis runs along the length of the field (horizontal)
  - Ranges from approximately -52.5m to +52.5m
  - Right side: (52.5, 0)
- Y-axis runs along the width of the field (vertical)
  - Ranges from approximately -34m to +34m
  - Top side: (0, 34)

Visual representation:
```
                    (0, 34)
                       ↑
                       |
    ←------------------+------------------→
                   (0, 0)              (52.5, 0)
                       |
                       ↓
    
    Center of pitch is at (0, 0)
    X-axis = length (left/right)
    Y-axis = width (up/down)
    Units are in meters
```

Physical Data (Aggregates):
The physical data is aggregated at a player-group-season level and contains the key metrics from our physical data. Documentation here: [link]
The dataset is filtered for performances above 60 mins only (sub players wouldn't appear unless they've played more than 60mins)

Dynamic Event Data:
The dynamic_events data is a CSV. Each row corresponds to a specific event_id belonging to 4 subcategories. Note:
- an event_id is unique to a game only
- the x/y attributes of each event are not scaled to standard pitchsize and require adjustment
For a full documentation of dynamic_events, refer to this documentation here

Phases of Play File:
The phase of play data is CSV. Each row corresponds to the start and end frames of a given phase
- Phases of play capture which phase the attacking and defending team are in concurrently.
- Phases of play are only defined when the ball is in play. When the ball is out of play there is no phase of play
- Each in-possession phase directly corresponds to an out-of-possession phase.
For detailed information on phases of play, refer to this documentation

Limitations:
TRACKING
- Some data points are erroneous. Around 97% of the player identity we provide are accurate.
- Some speed or acceleration smoothing and control should be applied to the raw data.

Working with the data:
In the Resources folder, we've provided an array of code and notebooks that provides a starting point to work with the tracking data. To get started visit the Kloppy tutorial or dive into the Tutorials Folder. SkillCorner customers will also find commented code they can use to connect to their match_ids using their credentials.

Online versions are available as well for:
- TRACKING Notebook: GoogleColab.
- SKILLCORNER VIZ visualization Library: GoogleColab

====================

Submission Requirements

Your submission should include:
- A video tutorial for first-time users
- A link to an online code repository (GitHub, etc) that includes:
  • All relevant files (EXCLUDING the dataset)
  • Any necessary helpers to run your tool (Dockerfile, etc) OR a link to your tool if it is available online
  • A README file that includes:
    • a description of your tool, including technical choices you made (libraries, languages, project structure, etc.) and clear instructions on how to use it
    • Information on tech stack and architecture
    • instructions on how to run your tool, including any dependencies (other than Docker, Python, etc) OR a link to your tool if it is available online

Evaluation Criteria

Submissions will be scored on a 1-5 basis on the following categories (1 = low, 5 = high):

- Technical feasibility: Could we switch out the game you used for this project and still use your tool? What does your tech stack look like? Do your technology choices make sense for the problem you've been asked to solve?
- Innovation: Was there anything novel about your project? Did you stick solely to the brief or sit in the shoes of a video analyst and think about what else might help them?
- Code quality: Is your code easy to understand? Does it have comments that explain your data processing? Is logic complex where it needs to be and simple where it doesn't? Are there obvious logic bugs?
- Presentation clarity: based on your demo of your project, can someone with limited computer experience beyond YouTube use pick up and understand how to use your tool?

The questions provided for each category are non-exhaustive and merely reference points to help guide your project design and execution.

Learning Resources

- SkillCorner overview: https://medium.com/skillcorner/a-new-world-of-performance-insight-from-video-tracking-technology-f0d7c0deb767
- SkillCorner data glossary: https://skillcorner.crunch.help/en/glossaries
- SkillCorner open data: https://github.com/SkillCorner/opendata
- Soccer analytics handbook: https://github.com/devinpleuler/analytics-handbook
- Friends of Tracking tutorials: https://www.youtube.com/channel/UCUBFJYcag8j2rm_9HkrrA7w
- McKay Johns tutorials: https://www.youtube.com/@McKayJohns/videos
- Application of SkillCorner Game Intelligence Data: https://medium.com/@carlon.carpenter/evaluating-movement-types-quality-in-the-final-third-00357b700efe
- Kloppy (a package commonly used to work with tracking data): https://github.com/PySport/kloppy
- Streamlit-soccer (a React module used to visualize tracking data): https://github.com/devinpleuler/streamlit-soccer


============IMPLEMENTATION============

Frontend/UI: Streamlit app using the streamlit-soccer React component for pitch animation + a Streamlit slider for scrubbing

Lib: streamlit, streamlit-soccer (React component wrapped for Streamlit) 
GitHub

Data ingest & model: kloppy to load/standardize SkillCorner OpenData tracking; gives you a vendor-agnostic TrackingDataset you can resample and normalize to pitch coords 
GitHub
+1

Source data: SkillCorner OpenData (pick any match); kloppy even has a direct loader for SkillCorner open data (load_open_data(match_id=...)) 
GitHub
+1

Clip export: imageio/Pillow + ffmpeg (or moviepy) to render 0–10s GIF/MP4 clips for share/download

API for long renders (optional): FastAPI endpoint (/render-clip) the Streamlit app calls; queue with RQ/Redis if you expect heavy loads

Persistence (optional): SQLite (local demo) or Supabase Postgres (cloud) to store clip metadata; object storage (S3/R2/Supabase Storage) for media blobs

Packaging/DevEx: uv/pip-tools, black/ruff, pytest, pre-commit; one-click run via Dockerfile

Deploy: Streamlit Community Cloud (fastest), or Fly.io/Render for the Streamlit+FastAPI pair

This aligns with the IRP brief’s goals (scrub timeline; clip 0–10 seconds; portable to any game) and the evaluation criteria around feasibility, clarity, and code quality. 

22-Oct-2025 GT IRP Hackathon

Minimal architecture

Streamlit (web UI)

Slider (frame index / timestamp)

TrackingComponent(frames=...) from streamlit-soccer to animate players/ball

“Set In/Out” buttons to capture a 0–10s window; “Render Clip” -> POST to /render-clip (or run inline for simplicity) 
GitHub

Data layer

kloppy.skillcorner.load_open_data(match_id=..., sample_rate=10 or 15) → standardized frames; cache with st.cache_data / st.cache_resource for speed 
Kloppy

Clip rendering

Convert frames in the selected window → images → GIF/MP4 (via imageio/ffmpeg); return a download link or Streamlit st.video() preview

Why these choices (briefly)

Feasibility/Swap-ability: kloppy abstracts the provider format; switching to a different SkillCorner match is just a different match_id. Future providers stay possible without re-wiring your viz. 
GitHub

Viz speed: streamlit-soccer already handles pitch + actors; you just feed frames (dicts/arrays) and control time with a slider. 
GitHub

Clear UX: Streamlit is dead simple to operate & demo; sliders + buttons mirror “video editor” muscle memory. (Also easy cloud deploy.) 
talking-tactics.com
+1

Suggested project layout
app/
  ├─ app.py                  # Streamlit UI: slider, in/out, preview
  ├─ loaders.py              # kloppy data loaders & caching
  ├─ transforms.py           # resampling, coordinate normalization
  ├─ render.py               # GIF/MP4 rendering utilities (imageio/ffmpeg)
  ├─ api.py                  # Optional FastAPI for /render-clip
  ├─ components/             # Any custom UI helpers
  ├─ assets/                 # Pitch overlays, team badges (optional)
  ├─ requirements.txt / pyproject.toml
  └─ Dockerfile

Key implementation notes

Loading data:

from kloppy import skillcorner
ds = skillcorner.load_open_data(match_id="1925299", sample_rate=10, include_empty_frames=False)
# Convert ds.frames → list of {players:[{id,x,y,team}], ball:{x,y,z}, ...} for streamlit-soccer


load_open_data pulls straight from the SkillCorner OpenData repo; no manual download needed. 
Kloppy

Scrubbing: Streamlit st.slider with integer frames or seconds; map to dataset timestamps.

Clipping: Capture t_in, t_out (max 10s), slice frames, render with imageio.mimsave (GIF) or ffmpeg (MP4).

Performance: Precompute per-frame render payloads; cache with st.cache_data; downsample to 10–15 FPS to keep GIF sizes reasonable.

Shareability: Write clips to /clips/<uuid>.gif (local) or upload to S3-compatible storage and share the signed URL.

Libraries recap

streamlit, streamlit-soccer for UI/animation 
GitHub

kloppy for loading/standardizing tracking data (incl. SkillCorner) 
GitHub
+2
Kloppy
+2

numpy, pandas for frame ops; imageio/ffmpeg/moviepy for exports

Optional: fastapi, uvicorn, redis + rq for queued renders; supabase/boto3 for storage

If you want, I can spin up a tiny starter repo with app.py wired to streamlit-soccer, a SkillCorner loader via kloppy, and a working 0–10s GIF export so you can iterate from there.