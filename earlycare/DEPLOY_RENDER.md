Render deployment (permanent public links)

Prerequisites
- Push this repository to GitHub.
- Create a free MongoDB Atlas database and copy its connection string.

Deploy with Blueprint (recommended)
1. In Render dashboard, click New + -> Blueprint.
2. Connect your GitHub repository.
3. Render detects `earlycare/render.yaml` and creates two Docker services:
   - `earlycare-backend`
   - `earlycare-frontend`
4. Set backend environment variables in Render:
   - `MONGO_URI` = your Atlas URI
   - `JWT_SECRET` = a long random secret
   - `GEMINI_API_KEY` = optional (if you use Gemini features)
5. Deploy services.

Important after first deploy
- Update frontend env var `BACKEND_UPSTREAM` to the actual backend public URL shown by Render,
  for example: `https://earlycare-backend.onrender.com`
- Trigger a redeploy of `earlycare-frontend`.

Public links
- Frontend: `https://<your-frontend-service>.onrender.com`
- Backend: `https://<your-backend-service>.onrender.com`

Notes about free tier
- Render free web services are available.
- Free services can sleep after inactivity and wake on next request.
