#!/bin/sh
# Fallback start script if Railpack is used; main deploy should use Dockerfile (railway.json: builder DOCKERFILE)
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
