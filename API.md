# C-Runner API 상세 문서

이 문서는 C-Runner API 서버의 상세 사용법과 예제를 제공합니다.

## 목차
- [API 개요](#api-개요)
- [API 엔드포인트](#api-엔드포인트)
- [요청 및 응답 형식](#요청-및-응답-형식)
- [테스트 케이스](#테스트-케이스)
  - [기본 실행 예제](#기본-실행-예제)
  - [명령행 인수 사용 예제](#명령행-인수-사용-예제)
  - [파일 입출력 예제](#파일-입출력-예제)
  - [에러 케이스 예제](#에러-케이스-예제)
- [실행 환경 격리 상세](#실행-환경-격리-상세)

## API 개요

C-Runner API는 웹 환경에서 C 코드를 안전하게 실행하고 결과를 반환하는 서비스입니다. 이 API를 통해 C 코드를 컴파일하고 실행한 후, 표준 출력, 표준 에러, 종료 코드를 JSON 형식으로 받을 수 있습니다.

## API 엔드포인트

- **URL**: `/execute_c`
- **메서드**: POST
- **Content-Type**: application/json

## 요청 및 응답 형식

### 요청 형식
```json
{
  "code": "C 코드 문자열",
  "args": "명령행 인수 (선택사항)"
}
```

#### 필드 설명
- `code` (필수): 실행할 C 소스 코드 문자열
- `args` (선택): 프로그램 실행 시 전달할 명령행 인수

### 응답 형식
```json
{
  "output": "표준 출력 결과",
  "error": "표준 에러 출력 또는 에러 메시지", 
  "exit_code": "종료 코드 (정수)"
}
```

#### 필드 설명
- `output`: 프로그램의 표준 출력(stdout) 결과
- `error`: 프로그램의 표준 에러(stderr) 출력 또는 컴파일 에러 메시지
- `exit_code`: 프로그램의 종료 코드 (0은 정상 종료, 다른 값은 에러 발생)

### 에러 응답 형식
잘못된 요청 시 다음과 같은 에러 메시지를 반환합니다:
```json
{
  "error": "에러 메시지"
}
```

## 테스트 케이스

테스트에서 사용하는 주소(`http://localhost:5555/execute_c`)에 서버를 띄우는 법은 README의 _빌드 및 실행 방법_ 을 참고해주세요. 


### 기본 실행 예제

간단한 "Hello World" 프로그램을 실행하는 예제입니다.

#### 요청
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"code": "#include <stdio.h>\nint main() { printf(\"Hello from C!\"); return 0; }"}' \
  'http://localhost:5555/execute_c'
```

#### 응답
```json
{
  "error": "",
  "exit_code": 0,
  "output": "Hello from C!"
}
```

### 명령행 인수 사용 예제

C 프로그램에 명령행 인수를 전달하는 예제입니다.

#### 요청
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"code": "#include <stdio.h>\nint main(int argc, char *argv[]) { printf(\"Args: %d\\n\", argc); for(int i=0; i<argc; i++) printf(\"%s\\n\", argv[i]); return 0; }", "args": "hello world 123"}' \
  'http://localhost:5555/execute_c'
```

#### 응답
```json
{
  "error": "",
  "exit_code": 0,
  "output": "Args: 4\n./tmp/c_exec_007dce3a-bae3-4c64-95f0-78f77a3a89f3/source\nhello\nworld\n123\n"
}
```

### 파일 입출력 예제

#### 단일 파일 읽기/쓰기 예제

C 프로그램에서 파일을 생성하고 읽는 예제입니다.

##### 요청
```bash
curl -X POST \
-H "Content-Type: application/json" \
-d '{"code": "#include <stdio.h>\n#include <string.h>\nint main() {\n    // 파일 쓰기\n    FILE *fp = fopen(\"test.txt\", \"w\");\n    if (fp) {\n        fprintf(fp, \"Hello, File I/O!\\n\");\n        fprintf(fp, \"Line 2\\n\");\n        fclose(fp);\n    }\n    \n    // 파일 읽기\n    fp = fopen(\"test.txt\", \"r\");\n    if (fp) {\n        char buffer[100];\n        printf(\"File contents:\\n\");\n        while (fgets(buffer, sizeof(buffer), fp)) {\n            printf(\"%s\", buffer);\n        }\n        fclose(fp);\n    }\n    return 0;\n}"}' \
'http://localhost:5555/execute_c'
```

##### 응답
```json
{
    "error": "",
    "exit_code": 0,
    "output": "File contents:\nHello, File I/O!\nLine 2\n"
}
```

#### 여러 파일 생성 및 처리 예제

여러 파일을 생성하고 읽는 예제입니다.

##### 요청
```bash
curl -X POST \
-H "Content-Type: application/json" \
-d '{"code": "#include <stdio.h>\n#include <stdlib.h>\nint main() {\n    // 여러 파일 생성\n    for (int i = 1; i <= 3; i++) {\n        char filename[20];\n        sprintf(filename, \"file%d.txt\", i);\n        FILE *fp = fopen(filename, \"w\");\n        if (fp) {\n            fprintf(fp, \"This is file number %d\\n\", i);\n            fclose(fp);\n            printf(\"Created %s\\n\", filename);\n        }\n    }\n    \n    // 파일들 읽어서 출력\n    printf(\"\\nReading files:\\n\");\n    for (int i = 1; i <= 3; i++) {\n        char filename[20];\n        sprintf(filename, \"file%d.txt\", i);\n        FILE *fp = fopen(filename, \"r\");\n        if (fp) {\n            char buffer[100];\n            while (fgets(buffer, sizeof(buffer), fp)) {\n                printf(\"%s: %s\", filename, buffer);\n            }\n            fclose(fp);\n        }\n    }\n    return 0;\n}"}' \
'http://localhost:5555/execute_c'
```

##### 응답
```json
{
    "error": "",
    "exit_code": 0,
    "output": "Created file1.txt\nCreated file2.txt\nCreated file3.txt\n\nReading files:\nfile1.txt: This is file number 1\nfile2.txt: This is file number 2\nfile3.txt: This is file number 3\n"
}
```

### 에러 케이스 예제

#### 컴파일 에러 예제

문법 오류가 있는 C 코드를 실행하는 예제입니다.

##### 요청
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"code": "#include <stdio.h>\nint main() { printf(\"Hello\" return 0; }"}' \
  'http://localhost:5555/execute_c'
```

##### 응답
```json
{
  "error": "/tmp/c_exec_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/source.c:2: error: expected ';' before 'return'\n",
  "exit_code": 1,
  "output": ""
}
```

#### 런타임 에러 예제

실행 중 오류가 발생하는 C 코드를 실행하는 예제입니다.

##### 요청
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"code": "#include <stdio.h>\nint main() { int *p = NULL; *p = 5; return 0; }"}' \
  'http://localhost:5555/execute_c'
```

##### 응답
```json
{
  "error": "",
  "exit_code": -11,
  "output": ""
}
```

#### 잘못된 요청 형식 예제

필수 필드가 누락된 요청을 보내는 예제입니다.

##### 요청
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"invalid": "request"}' \
  'http://localhost:5555/execute_c'
```

##### 응답
```json
{
  "error": "Missing required field: 'code'"
}
```

## 실행 환경 격리 상세

각 C 코드 실행은 다음과 같이 격리된 환경에서 수행됩니다:

1. **파일 시스템 제한**: `/tmp` 디렉토리에서만 파일 읽기/쓰기 가능, 나머지는 read-only
2. **고유 작업 디렉터리**: `/tmp/c_exec_{UUID}` 형태의 디렉터리 생성
3. **독립적인 파일 시스템**: 각 실행마다 별도의 작업 공간 제공
4. **자동 정리**: 실행 완료 후 작업 디렉터리 및 모든 임시 파일 삭제
5. **타임아웃 보호**: 10초 초과 시 프로세스 강제 종료

이를 통해 여러 요청이 동시에 들어와도 서로 간섭하지 않고 안전하게 실행됩니다.

### 보안 고려사항

단, `/tmp` 작업 디렉터리 간 하위 파일 전체를 삭제하거나 하는 등의 동작을 통해 간섭이 가능할 수 있습니다.    
프로덕션 환경에서 사용하려면 격리된 사용자가 서로 간섭하지 못하게 막는 추가적인 보안 처리가 필요합니다.

## 프로젝트 개요 및 기본 정보

프로젝트 개요 및 기본 정보는 [README](./README.md)를 참조하세요.
