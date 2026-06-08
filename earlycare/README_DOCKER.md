Docker deployment instructions for EarlyCare

1) Copy environment variables

   - Create `backend/.env` from `backend/.env.example` and fill any secrets.

2) Build and start services

```bash
cd earlycare
docker compose up --build -d
```

3) App URLs

- Frontend: http://localhost:5177
- Backend API: http://localhost:5002

4) Notes

- Tesseract OCR and other native dependencies are installed in the backend image.
- Models and uploaded files are mounted from `backend/models` and `backend/uploads`.
- To stop and remove containers: `docker compose down -v`.
