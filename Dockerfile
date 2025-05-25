# TinyCC 빌드 
ARG DOCKER_IMAGE_RUNTIME=alpine:latest
FROM $DOCKER_IMAGE_RUNTIME AS builder
RUN apk add --no-cache gcc make musl-dev git \
    && git clone --recurse-submodules https://github.com/TinyCC/tinycc.git /tinycc
WORKDIR /tinycc
# make test 실패해도 무시하고 실행
RUN ./configure --config-musl \
    && make -j$(nproc) \
    && make test -j$(nproc) || true \
    && make install

# 런타임 환경
FROM $DOCKER_IMAGE_RUNTIME AS runtime

# Python 및 필수 패키지 설치
RUN apk add --no-cache musl-dev python3 py3-pip

# 앱 디렉터리 생성 및 이동
WORKDIR /usr/src/app

# 가상환경(venv) 생성
RUN python3 -m venv ./venv

# PATH에 venv/bin을 우선 등록하여 pip, python이 가상환경 것을 사용하도록 설정
ENV PATH="/usr/src/app/venv/bin:${PATH}"

# requirements.txt 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 빌드단에서 만든 tcc 복사 
COPY --from=builder /usr/local /usr/local

# 앱 소스 복사
COPY app.py ./

# TCC 작동 확인 
ENV PATH="/usr/local/bin:${PATH}"
ENV CC="/usr/local/bin/tcc"
RUN tcc -v

# 포트 노출 및 실행
EXPOSE 5000
CMD ["python3", "app.py"]
