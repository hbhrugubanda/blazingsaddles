.PHONY: test
test:
	py.test --cov=app

.PHONY: test-buildcov
test-buildcov:
	py.test --cov=app && (echo "building coverage html, view at './htmlcov/index.html'"; coverage html)
