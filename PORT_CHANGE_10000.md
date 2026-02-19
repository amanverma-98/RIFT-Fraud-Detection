# Port Update: 8000 → 10000

## Reason
Updated from port 8000 to port 10000 for compatibility with Render deployment (Render automatically uses port 8000).

## Files Updated (4 files)

### 1. app/config.py
```python
# Line 16: Updated default port
port: int = 10000  # Changed from 8000
```

### 2. .env.example
```bash
# Line 8: Updated example environment variable
PORT=10000  # Changed from 8000
```

### 3. Dockerfile
```dockerfile
# Line 27: Updated exposed port
EXPOSE 10000  # Changed from 8000

# Line 30: Updated command argument
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "2"]
#                                                                    ^^^^^ Changed from 8000
```

### 4. docker-compose.yml
```yaml
# Line 10: Updated port mapping
ports:
  - "10000:10000"  # Changed from "8000:8000"

# Line 16: Updated environment variable
- PORT=10000  # Changed from PORT=8000

# Line 25: Updated healthcheck endpoint
test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:10000/api/health').read()"]
#                                                                                              ^^^^^ Updated from 8000
```

## Deployment Instructions

### Local Testing (Port 10000)
```bash
# With Docker Compose
docker-compose up -d

# Access application
curl http://localhost:10000/api/health
curl http://localhost:10000/docs
```

### Render Cloud Deployment
Render will automatically forward external traffic to internal port 10000:

```bash
# Your custom domain will be available at
https://your-app.onrender.com

# Internal port 10000 is automatically bound
# No additional configuration needed
```

## Verification Checklist

- [x] app/config.py default port = 10000
- [x] .env.example PORT = 10000
- [x] Dockerfile EXPOSE = 10000
- [x] Dockerfile CMD uses --port 10000
- [x] docker-compose.yml ports = 10000:10000
- [x] docker-compose.yml PORT env var = 10000
- [x] Healthcheck endpoint uses port 10000
- [x] All changes consistent across files

## Testing After Update

### Docker Local Test
```bash
docker-compose down
docker-compose up -d

# Wait for container to start
sleep 5

# Check health
curl http://localhost:10000/api/health

# Check API docs
curl http://localhost:10000/docs
```

### Expected Response
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "app_name": "Fraud Detection System"
}
```

## Render Deployment Configuration

Update your `render.yaml` or Render dashboard:

```yaml
services:
  - type: web
    name: fraud-detection-system
    env: docker
    plan: free
    
    # Render will expose your app at the above port
    # No need to configure port here - it auto-maps 10000
```

Render's routing:
- External: `https://your-app.onrender.com` → port 443 (HTTPS)
- Internal: Application port 10000
- Automatic forwarding (no manual configuration needed)

**Status**: ✅ Ready for Render deployment on port 10000
