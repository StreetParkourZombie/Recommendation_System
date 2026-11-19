FROM tensorflow/tensorflow:1.14.0-py3

LABEL org.opencontainers.image.title="Paper 01 data leakage reproduction"
LABEL org.opencontainers.image.description="Legacy runtime for Ji et al. TOIS 2023 reproduction code"

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 TF_CPP_MIN_LOG_LEVEL=1 CUDA_VISIBLE_DEVICES=""
WORKDIR /workspace
COPY requirements-bpr-neumf.txt /tmp/requirements-bpr-neumf.txt
RUN python -m pip install --no-cache-dir \
        "pip==20.3.4" \
        "setuptools==44.1.1" \
        "wheel==0.36.2" \
    && python -m pip install --no-cache-dir --prefer-binary -r /tmp/requirements-bpr-neumf.txt
CMD ["python", "--version"]
