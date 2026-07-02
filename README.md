# motion — Single Image to Video Generator

Generate videos from a **single start image** plus a motion prompt using the Replicate API. Supports prompt prefix/suffix modifications and multiple terminal output modes.

## Prerequisites

- Python 3.10+
- [Replicate](https://replicate.com) API key (set via `REPLICATE_API_TOKEN` env var or 1Password)
- (Optional) [1Password CLI](https://developer.1password.com/docs/cli/) — for retrieving API tokens from 1Password vaults

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Input Format

Place `.md` files in `USER-FILES/04.INPUT/`. Each file must contain **3 lines**:

```
A cinematic tracking shot through a forest
120
![image](https://example.com/my_image.jpg)
```

| Line | Field | Description |
|------|-------|-------------|
| 1 | prompt | Motion description (free text) |
| 2 | num_frames | Number of frames (positive integer) |
| 3 | image_url | Image URL in markdown `![alt](url)` format |

The 3rd line **must** use markdown image syntax — raw URLs are not accepted.

## Usage

Three entry points provide different terminal output styles:

```bash
# Basic mode (simple progress bar)
python -m src.main

# Verbose mode (Rich console output with emoji indicators)
python -m src.main_verbose

# Hybrid mode (alive-progress WAVES animation + Rich logging)
python -m src.main_hybrid
```

The `run.py` script launches `src.main_verbose` by default:

```bash
./run.py
```

### Cost Estimation (dry run)

```bash
python -m src.estimate_costs
```

## Prompt Prefix/Suffix

Profiles can automatically prepend/append text to every prompt:

```yaml
prompt_prefix: "Cinematic style:"
prompt_suffix: "Shot on ARRI Alexa, 4K resolution"
```

If both are configured, the final prompt becomes: `{prefix} {original} {suffix}`.

## Output

Output is written to a timestamped directory in `USER-FILES/05.OUTPUT/`:

```
video_YYMMDD_HHMMSS.mp4          — Generated video
video_YYMMDD_HHMMSS_payload.json — API request/response
video_YYMMDD_HHMMSS_report.md    — Per-video report
video_YYMMDD_HHMMSS.log          — Generation log
```

Run-level reports (`SUCCESS.md`, `cost_report.md`, `ADJUSTMENTS.md`) are also generated.

## Profile Configuration

Create a YAML profile in `USER-FILES/03.PROFILES/`:

```yaml
project: "MY PROJECT"
paths:
  input: "/custom/input/path"
  output: "/custom/output/path"

prompt_suffix: " cinematic quality, smooth motion"

Model:
  endpoint: provider/model-name:version
  code-nickname: my-model

pricing:
  cost_per_second: 0.01

duration_type: seconds
fps: 24
duration_min: 5
duration_max: 10
duration_param_name: duration

params:
  aspect_ratio: "16:9"
```

### Custom Paths

- `paths.input` — Override the default input directory (default: `USER-FILES/04.INPUT/`)
- `paths.output` — Override the default output directory (default: `USER-FILES/05.OUTPUT/`)
- Paths are validated at startup — non-existent paths cause immediate failure

Exactly one profile must be active when running.

## Dependencies

- `replicate` — Replicate API client
- `loguru` — Logging
- `rich` — Rich console output (verbose/hybrid modes)
- `alive-progress` — Animated progress bars (hybrid mode)
- `natsort` — Natural sorting
- `pyyaml` — YAML parsing
- `requests` — HTTP downloads
