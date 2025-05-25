# 🚀 Blog Project - FastAPI Best Practices

A comprehensive starter kit that brings together industry-proven FastAPI patterns and real-world examples, helping both newcomers and seasoned engineers build robust, maintainable applications faster.

---

✨ Features

- Full asynchronous FastAPI application for high performance.
- Modular and extensible project architecture.
- SQLAlchemy ORM and PostgreSQL database integration.
- Automated database migrations with Alembic.
- Comprehensive authentication via fastapi-users (JWT, registration, login).
- API rate limiting using fastapi-limiter.
- Efficient data pagination with fastapi-pagination.
- Email sending functionality via fastapi-mail.
- Multi-language support powered by starlette-babel.
- Structured logging (console and rotating file outputs).
- Full-featured admin panel using SQLAdmin.
- Server-side rendering for frontend with Jinja2.
- Production-ready deployment using Docker Compose and Nginx.

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

[![FastAPI Blog Project Demo](https://img.youtube.com/vi/CzU4rLK_UTU/maxresdefault.jpg)](https://www.youtube.com/watch?v=CzU4rLK_UTU)
