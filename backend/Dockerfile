# 1. Use Python 3.10 as base
FROM python:3.10-slim

# 2. Create a new user named 'user' with ID 1000
RUN useradd -m -u 1000 user

# 3. Set the working directory
WORKDIR /app

# --- FIX: Give the user ownership of the /app folder immediately ---
RUN chown user:user /app

# 4. Switch to the new user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 5. Install dependencies
COPY --chown=user:user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY --chown=user:user . .

# 7. Create the uploads directory (This will now work!)
RUN mkdir -p uploaded_data && chmod 777 uploaded_data

# 8. Expose port 7860 (Hugging Face specific port)
EXPOSE 7860

# 9. Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]