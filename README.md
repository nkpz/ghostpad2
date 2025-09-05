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

## Demos

System Prompt Construction


https://github.com/user-attachments/assets/5df8e2fa-4f78-4295-8075-a4e3ac201000


Web Browser Simulator Tool



https://github.com/user-attachments/assets/2e697181-a7cb-4f50-98c0-52e2e151858b



Private Messages Tool


https://github.com/user-attachments/assets/c324fc96-ba5c-47cb-b056-11bdf4cb0a66


Combat Tool: Fighting The Assistant



https://github.com/user-attachments/assets/f74184af-ff15-4624-8842-dd54b9d68a97


Combat Tool: Fighting A Spawned Enemy




https://github.com/user-attachments/assets/aee21b19-d75f-41f0-95c1-0771fcedd033


