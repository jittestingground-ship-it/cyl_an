
import platform
import sys
import os
import subprocess
import time
import tkinter as tk


# Use system Python first, then venv if needed
VENV_PYTHON = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
SYSTEM_PYTHON = sys.executable

def get_installed_packages(python_exec):
    try:
        result = subprocess.check_output([python_exec, '-m', 'pip', 'freeze'])
        return result.decode().splitlines()
    except Exception:
        return []

# Collect system info
def get_system_info():
    info = {
        'os': platform.platform(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': sys.version,
        'cwd': os.getcwd(),
    }
    return info

# Check for port conflicts (5050)
def check_port_conflict(port=5050):
    try:
        result = subprocess.check_output(f"lsof -i :{port}", shell=True, stderr=subprocess.STDOUT)
        return result.decode()
    except subprocess.CalledProcessError:
        return None

# Check installed Python packages

# Run two diagnostic tests
def run_diagnostics():
    # Run pip check and pip show flask for both system and venv
    def run_pip_check(python_exec):
        try:
            result = subprocess.check_output([python_exec, '-m', 'pip', 'check'])
            return result.decode().strip()
        except subprocess.CalledProcessError as e:
            return e.output.decode().strip() if e.output else str(e)
    def run_pip_show_flask(python_exec):
        try:
            result = subprocess.check_output([python_exec, '-m', 'pip', 'show', 'flask'])
            return result.decode().strip()
        except subprocess.CalledProcessError as e:
            return e.output.decode().strip() if e.output else 'Flask not installed.'

    results = []
    sys_info_sys = get_system_info()
    port_conflict_sys = check_port_conflict()
    packages_sys = get_installed_packages(SYSTEM_PYTHON)
    required = ['flask', 'playwright']
    missing_sys = [pkg for pkg in required if not any(pkg in p for p in packages_sys)]
    pip_check_sys = run_pip_check(SYSTEM_PYTHON)
    pip_show_sys = run_pip_show_flask(SYSTEM_PYTHON)
    results.append(('SYSTEM PIP CHECK', pip_check_sys))
    results.append(('SYSTEM PIP SHOW FLASK', pip_show_sys))
    results.append(('SYSTEM PYTHON INFO', sys_info_sys))
    results.append(('SYSTEM PORT CONFLICT', 'Port conflict detected' if port_conflict_sys else 'No port conflict'))
    results.append(('SYSTEM PACKAGE CHECK', f'Missing packages: {missing_sys}' if missing_sys else 'All required packages installed'))

    # If missing packages, switch to venv and run diagnostics there
    if missing_sys and os.path.exists(VENV_PYTHON):
        sys_info_venv = get_system_info()
        port_conflict_venv = check_port_conflict()
        packages_venv = get_installed_packages(VENV_PYTHON)
        missing_venv = [pkg for pkg in required if not any(pkg in p for p in packages_venv)]
        pip_check_venv = run_pip_check(VENV_PYTHON)
        pip_show_venv = run_pip_show_flask(VENV_PYTHON)
        results.append(('VENV PIP CHECK', pip_check_venv))
        results.append(('VENV PIP SHOW FLASK', pip_show_venv))
        results.append(('VENV PYTHON INFO', sys_info_venv))
        results.append(('VENV PORT CONFLICT', 'Port conflict detected' if port_conflict_venv else 'No port conflict'))
        results.append(('VENV PACKAGE CHECK', f'Missing packages: {missing_venv}' if missing_venv else 'All required packages installed'))
    return results

# Simple Tkinter UI for results and actions
def show_results():
    results = run_diagnostics()
    root = tk.Tk()
    root.title('Dashboard Self-Diagnosis')
    text = tk.Text(root, width=80, height=30)
    text.pack(padx=10, pady=10)
    for label, value in results:
        text.insert('end', f'{label}:\n')
        if isinstance(value, dict):
            for k, v in value.items():
                text.insert('end', f'  {k}: {v}\n')
        else:
            text.insert('end', f'  {value}\n')
        text.insert('end', '\n')
    fix_btn = tk.Button(root, text='Fix', command=lambda: text.insert('end', '\nAuto-fix not implemented yet.'))
    fix_btn.pack(side='left', padx=20, pady=10)
    exit_btn = tk.Button(root, text='Exit', command=root.destroy)
    exit_btn.pack(side='right', padx=20, pady=10)
    root.mainloop()

if __name__ == '__main__':
    show_results()
