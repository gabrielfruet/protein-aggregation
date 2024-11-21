FROM tensorflow/tensorflow:latest-gpu-jupyter

WORKDIR /usr/src/work

COPY ./pyproject.toml ./pyproject.toml
COPY ./README.md ./README.md

RUN apt-get update -y

RUN apt-get install graphviz -y

RUN python3 -m pip install --upgrade pip

RUN pip install .[all]

RUN pip install jupyterlab pydot pydot_ng

EXPOSE 8888

CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
