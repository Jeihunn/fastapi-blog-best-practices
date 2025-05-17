# 🚀 Blog Project - FastAPI Best Practices

This template summarizes the core principles of developing applications with FastAPI through practical examples, providing a reliable starting point for both beginners and experienced developers.

---

## ✨ Features

- High performance with asynchronous operations
- Modular and extensible architecture
- Robust authentication and authorization mechanisms
- Automated database migrations
- Multi-language support and admin panel
- Structured logging: detailed logs written to the console and rotating files
- Server-rendered frontend using Jinja2 templates
- Unified development and deployment environment with Docker

---

## 💻 Requirements

- Python ≥ 3.11
- Docker and Docker Compose
- Git

---

## ⬇️ Installation

1. Clone the project and navigate into the directory:

   ```bash
   git clone https://github.com/Jeihunn/fastapi-blog-best-practices.git
   cd fastapi-blog-best-practices
   ```

2. Install project dependencies:

   ```bash
   pip install -r requirements/local.txt
   ```

3. Copy the sample `.env.local` file to `.env` and fill in the required parameters.

4. Build the Docker images and start the containers:

   ```bash
   cd docker/local/
   docker-compose up -d
   ```

5. Apply the database schema migrations:

   ```bash
   alembic upgrade head
   ```

6. Run the application:

   ```bash
   fastapi dev src/main.py
   ```

7. Open your browser and check:
   - Home page: `http://localhost:8000`
   - Swagger UI (API docs): `http://localhost:8000/docs`
   - Admin panel: `http://localhost:8000/admin`

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📺 Video

Demo showcasing the project in action

[![FastAPI Blog Project Demo](https://img.youtube.com/vi/fixMe/maxresdefault.jpg)](https://www.youtube.com/watch?v=fixMe)
