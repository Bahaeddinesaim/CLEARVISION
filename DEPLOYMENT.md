# GitHub and Streamlit Deployment

This project is ready to be pushed to GitHub without local private data.

## What is ignored

The repository excludes generated and personal files:

- `data/**` outputs, uploads, CSV files, reports and SQLite database
- `.streamlit/secrets.toml`
- `.env`
- local model weights such as `*.pt`
- uploaded images and audio files

Only `.gitkeep` files are kept so the folder structure exists on a fresh clone.

## First GitHub push

```bash
git init
git add .
git commit -m "Initial ClassVision AI app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Before pushing, check what will be committed:

```bash
git status --short
git check-ignore -v data/raw/raw_detections.csv data/classvision.db yolo11n.pt
```

The second command should confirm that local data/model files are ignored.

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app from your GitHub repository.
4. Set the main file path to `app.py`.
5. Deploy.

On first launch, the app creates fresh local runtime folders with `ensure_directories()`.
No local CSV, images, audio files or SQLite database are required from your machine.

## Important note about YOLO weights

`*.pt` files are ignored to avoid committing large local model weights. If the YOLO model is not available in deployment, the app falls back to simulated detections instead of crashing.

For a production deployment, use a model artifact strategy:

- download the model at startup from a controlled storage location
- or store it in a private artifact registry
- or configure the deployment environment to provide it

Do not commit private datasets, classroom photos, audio samples, SQLite databases or secrets.

## GitHub Pages

GitHub Pages can host only static files. It cannot run the Streamlit Python app directly.

This repository includes a static showcase page in:

```text
docs/index.html
```

To publish it:

1. Push the repository to GitHub.
2. Open the GitHub repository settings.
3. Go to `Pages`.
4. Select `Deploy from a branch`.
5. Choose branch `main`.
6. Choose folder `/docs`.
7. Save.

Your static page will be available at:

```text
https://bahaeddinesaim.github.io/CLEARVISION/
```

The interactive Streamlit app must be deployed somewhere that runs Python, for example Streamlit Community Cloud, Docker on a server, Render, Railway or Hugging Face Spaces.

## Local LAN URL

To expose the local Streamlit app on your network:

```powershell
.\scripts\start_lan.ps1
```

Or run:

```powershell
streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

Then open:

```text
http://10.68.247.21:8502
```

This URL works only while your computer is running Streamlit and other devices are on the same network. If it does not open, allow Python/Streamlit through Windows Firewall for private networks.
