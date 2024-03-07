run:
	docker build -t space-drive-backend .
	docker run -p 3334:3334 space-drive-backend
lint:
	flake8
	find . -iname "*.py" -path "./src/*" | xargs pylint
	isort . --check-only
fix:
	isort .
