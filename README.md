# Ghostpad

An OpenAI API compatible text generation frontend with a powerful tools API.

## Quick Start

On Mac or Linux, you will need to install Python and Node (Recommended instructions: https://chatgpt.com/s/t_68ba0bb0203c8191ac1c26a4ce4eb395).

On Windows, the start script will install these automatically if they aren't present.

Simply run:

```bash
./start.sh
```

or on Windows:

```
start.cmd
```

This will automatically:

- Install uv (via pip if not available)
- Create a virtual environment
- Install Python dependencies
- Build the React frontend (if needed)
- Start the server at http://127.0.0.1:8000

## Architecture

- **FastAPI Backend**: Serves API routes under `/api/` prefix
- **React Frontend**: Built with Vite, served from root route
- **Single Server**: FastAPI serves both API and static files
