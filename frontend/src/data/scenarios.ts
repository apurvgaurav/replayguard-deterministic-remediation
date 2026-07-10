export interface Scenario {
  id: string;
  name: string;
  description: string;
  language: string;
  code: string;
}

export const fallbackScenarios: Scenario[] = [
  {
    id: "sql_injection",
    name: "SQL Injection via Concatenation",
    description: "Vulnerable SQL query construction using string concatenation, which allows SQL injection.",
    language: "python",
    code: "def get_user(user_id):\n    query = \"SELECT * FROM users WHERE id = \" + user_id\n    return db.execute(query)"
  },
  {
    id: "hardcoded_secret",
    name: "Hardcoded API Key Credential",
    description: "Plaintext secret committed to source code, risking exposure in repositories.",
    language: "python",
    code: "def connect_api():\n    API_KEY = \"abc123secret\"\n    return connect(API_KEY)"
  },
  {
    id: "unsafe_shell",
    name: "Unsafe Shell Execution",
    description: "Executing system shell commands with user-supplied arguments via shell=True, risking command injection.",
    language: "python",
    code: "import subprocess\n\ndef cleanup_temp(path):\n    subprocess.run(\"rm -rf \" + path, shell=True)"
  },
  {
    id: "replay_mismatch_block",
    name: "Replay Mismatch - Block Merge",
    description: "A deterministic remediation run is intentionally made inconsistent during the second replay run to demonstrate that ReplayGuard blocks the merge when byte-level verification fails.",
    language: "python",
    code: "query = \"SELECT * FROM users WHERE id = \" + user_id"
  },
  {
    id: "no_template_review",
    name: "No Template - Human Review Required",
    description: "A vulnerability-like issue is detected, but no deterministic remediation template exists. ReplayGuard should not patch it and should route it to human review.",
    language: "python",
    code: "eval(user_input)"
  }
];
