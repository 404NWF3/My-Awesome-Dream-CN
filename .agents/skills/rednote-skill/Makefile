.PHONY: build install install-dev clean

# 构建 .whl 安装包到 dist/
build:
	python3 -m build --wheel

# 从 .whl 文件安装（先 build）
install: build
	python3 -m pip install dist/rednote-*.whl

# 开发模式安装（代码修改即时生效）
install-dev:
	python3 -m pip install -e .

# 清理构建产物
clean:
	rm -rf dist/ build/ *.egg-info rednote.egg-info
