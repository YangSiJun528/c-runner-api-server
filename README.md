# C-Runner API 서버

## 프로젝트 소개
C-Runner API는 웹 환경에서 C 코드를 실행할 수 있는 간단한 API 서비스입니다. 

Flask 서버와 TinyCC(TCC) 컴파일러를 사용해 C 코드를 컴파일하고 실행 결과를 JSON으로 반환합니다.

## 개발 목적
Markdown 기반 정적 사이트에서 C 코드블럭을 바로 실행할 수 있게 하기 위한 백엔드 서비스로 개발되었습니다.

## 주의사항
- **프로덕션 환경 사용 금지**: 이 서버는 사용자 제공 C 코드를 직접 실행하므로 보안 위험이 있습니다.
- 프로덕션에 배포하려면 다음 사항을 구현해야 합니다:
  - API 접근 제한 및 인증 메커니즘 추가
  - CORS 설정 제한 (현재는 모든 도메인 허용)
  - 코드 실행 샌드박스 강화
  - 등등

## 프로젝트 구조
```
.
├── Dockerfile      # 도커 이미지 빌드 설정 - TCC 구성 포함
├── LICENSE         # 라이선스 정보
├── README.md       # 프로젝트 설명서
├── app.py          # Flask API 서버 코드
└── requirements.txt # Python 의존성 패키지
```

## 빌드 및 실행 방법

### 도커 이미지 빌드
```bash
docker build -t c-runner-api-server .
```

### 도커 컨테이너 실행
```bash
docker run -d -p 5555:5000 --name c-runner c-runner-api-server
```
- 포트 매핑: 호스트 5555 → 컨테이너 5000
- 필요시 포트 번호 변경 가능

## API 사용법

### 엔드포인트
- **URL**: `http://localhost:5555/execute_c`
- **메서드**: POST
- **Content-Type**: application/json

### 요청 형식
```json
{
  "code": "C 코드 문자열"
}
```

### 응답 형식
```json
{
  "output": "표준 출력 결과",
  "error": "표준 에러 출력 또는 에러 메시지",
  "exit_code": 종료 코드 (정수)
}
```

## 테스트 케이스

성공적으로 배포 되었는지 확인할 때 유용함.

### 성공 케이스
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"code": "#include <stdio.h>\nint main() { printf(\"Hello from C!\"); return 0; }"}' \
  'http://localhost:5555/execute_c'
```

예상 응답:
```json
{
  "error": "",
  "exit_code": 0,
  "output": "Hello from C!"
}
```

### 컴파일 에러 케이스
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"code": "#include <stdio.h>\nint main() { printf(\"Hello\" return 0; }"}' \
  'http://localhost:5555/execute_c'
```

예상 응답:
```json
{
  "error": "/tmp/tmpXXXXXX.c:2: error: expected ';' before 'return'\n",
  "exit_code": 1,
  "output": ""
}
```


### 런타임 에러 케이스
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"code": "#include <stdio.h>\nint main() { int *p = NULL; *p = 5; return 0; }"}' \
  'http://localhost:5555/execute_c'
```

예상 응답:
```json
{
  "error": "",
  "exit_code": -11,
  "output": ""
}
```

# LICENSE

["MIT-0" License](./LICENSE)
