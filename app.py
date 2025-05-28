from flask import Flask, request, jsonify, make_response
import subprocess
import tempfile
import os
import html
import shlex
import uuid
import shutil


app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin']  = '*'                      # 모든 도메인 허용
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'     # 허용 메서드
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'           # 허용 헤더
    return response

@app.after_request
def add_referrer_policy(response):
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

# TCC 경로 (Docker 이미지 내 경로)
TCC_PATH = "/usr/local/bin/tcc"

@app.route('/health', methods=['GET'])
def health_check():
    return "OK"

@app.route('/execute_c', methods=['POST', 'OPTIONS'])
def execute_c():
    if request.method == 'OPTIONS':
        # 프리플라이트 요청에 빈 응답(204) 반환
        return make_response('', 204)
    
    # JSON body 유효성 검사
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON format"}), 400
    
    if data is None:
        return jsonify({"error": "No JSON body provided"}), 400
    
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 400
    
    if 'code' not in data:
        return jsonify({"error": "Missing required field: 'code'"}), 400
    
    if not isinstance(data['code'], str):
        return jsonify({"error": "Field 'code' must be a string"}), 400
    
    c_code = data['code']
    cli_args = data.get('args', '')  # Command line arguments (optional)
    
    # args 필드 타입 검사 (선택적 필드이므로 있을 때만 검사)
    if 'args' in data and not isinstance(data['args'], str):
        return jsonify({"error": "Field 'args' must be a string"}), 400
    
    output = ""
    error = ""
    exit_code = 0
    
    # 각 실행마다 고유한 작업 디렉터리 생성
    execution_id = str(uuid.uuid4())
    work_dir = os.path.join("/tmp", f"c_exec_{execution_id}")
    tmp_c_file_path = None
    
    try:
        # 작업 디렉터리 생성
        os.makedirs(work_dir, exist_ok=True)
        
        # Command line arguments 처리
        args_list = []
        if cli_args.strip():
            # 안전하게 문자열을 쉘 인수로 파싱
            args_list = shlex.split(cli_args)
        
        # 작업 디렉터리 내에 C 소스 파일 생성
        tmp_c_file_path = os.path.join(work_dir, "source.c")
        with open(tmp_c_file_path, 'w') as f:
            f.write(c_code)
        
        # tcc -run <source_file> [args...]
        compile_run_cmd = [TCC_PATH, "-run", tmp_c_file_path] + args_list
        
        process = subprocess.Popen(
            compile_run_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=work_dir  # 생성된 작업 디렉터리에서 실행
        )
        
        stdout_str, stderr_str = process.communicate(timeout=10) # 10초 타임아웃
        
        output = html.escape(stdout_str) # HTML 태그가 출력으로 나오는 것을 방지
        error = html.escape(stderr_str)
        exit_code = process.returncode
        
    except subprocess.TimeoutExpired:
        error = "Execution timed out after 10 seconds."
        exit_code = -1 # 타임아웃 시 특별한 종료 코드
        # 프로세스 강제 종료
        try:
            process.kill()
            process.wait()
        except:
            pass
    except Exception as e:
        error = f"An unexpected error occurred: {str(e)}"
        exit_code = -2 # 예외 발생 시
    finally:
        # 작업 디렉터리 전체 삭제 (C 소스파일 및 생성된 모든 파일 포함)
        try:
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir)
        except:
            pass  # 삭제 실패해도 무시 (어차피 /tmp라서 나중에 지워짐)
    
    return jsonify({
        "output": output,
        "error": error,
        "exit_code": exit_code
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)