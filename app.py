from flask import Flask, request, jsonify, make_response
import subprocess
import tempfile
import os
import html

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin']  = '*'                      # 모든 도메인 허용
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'     # 허용 메서드
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'           # 허용 헤더
    return response

@app.after_request
def add_referrer_policy(response):
    response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'  # 또는 'no-referrer'
    return response

# TCC 경로 (Docker 이미지 내 경로)
TCC_PATH = "/usr/local/bin/tcc"

@app.route('/execute_c', methods=['POST', 'OPTIONS'])
def execute_c():
    if request.method == 'OPTIONS':
        # 프리플라이트 요청에 빈 응답(204) 반환
        return make_response('', 204)

    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({"error": "No code provided"}), 400

    c_code = data['code']

    # 임시 C 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as tmp_c_file:
        tmp_c_file_name = tmp_c_file.name
        tmp_c_file.write(c_code)

    # 임시 실행 파일 경로 (TCC는 -o 없이도 실행 가능하지만, 명시적으로 제어)
    # TCC는 -run 옵션으로 컴파일과 실행을 동시에 할 수 있음
    # tmp_executable_name = tmp_c_file_name.replace(".c", "") # 사용하지 않음

    output = ""
    error = ""
    exit_code = 0

    try:
        # tcc -run <source_file> [args...]
        # 컴파일 및 실행, stdin/stdout/stderr 처리
        # Timeout을 설정하여 무한 루프 방지
        compile_run_cmd = [TCC_PATH, "-run", tmp_c_file_name]

        process = subprocess.Popen(
            compile_run_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Python 3.7+
        )
        
        # stdin이 필요한 경우를 위해 (현재는 미사용)
        # stdout_bytes, stderr_bytes = process.communicate(input=input_data_str, timeout=10) 
        
        stdout_str, stderr_str = process.communicate(timeout=10) # 10초 타임아웃
        
        output = html.escape(stdout_str) # HTML 태그가 출력으로 나오는 것을 방지
        error = html.escape(stderr_str)
        exit_code = process.returncode

    except subprocess.TimeoutExpired:
        error = "Execution timed out after 10 seconds."
        exit_code = -1 # 타임아웃 시 특별한 종료 코드
    except Exception as e:
        error = f"An unexpected error occurred: {str(e)}"
        exit_code = -2 # 예외 발생 시
    finally:
        # 임시 파일 삭제
        os.remove(tmp_c_file_name)
        # if os.path.exists(tmp_executable_name): # -run 사용 시 실행 파일이 남지 않음
        #     os.remove(tmp_executable_name)

    return jsonify({
        "output": output,
        "error": error,
        "exit_code": exit_code
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "health": "ok",
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)