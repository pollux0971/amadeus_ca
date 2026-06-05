# Risk and Safety

## 1. 主要風險

### R1. 誤刪檔案

CLI agent 可能執行破壞性命令。

對策：

- denylist：`rm -rf`, `del /s`, `format`, `sudo rm`
- workspace sandbox。
- git diff before promotion。
- high risk command 需要人工確認。

---

### R2. Secret 外洩

Agent 可能讀取 `.env`、API key、SSH key。

對策：

- block `.env`, `.ssh`, credential files。
- secret scanner。
- browser context 不可看到 secret。
- trace 中不可保存 raw secret。

---

### R3. Browser Prompt Injection

網頁可能要求 agent 忽略規則或執行 CLI command。

對策：

- Browser content 標記為 `untrusted_web`。
- Browser content 不可直接轉 CLI command。
- Safety Gate 檢查所有 browser-to-CLI 資訊。
- Adversarial tests。

---

### R4. Package Install 風險

`npm install` 或 `pip install` 可能執行 postinstall script 或下載惡意套件。

對策：

- 第一版只允許 fixtures。
- package install 需要人工審核。
- CI sandbox。
- disable scripts when possible。

---

### R5. Auto Repair Regression

Claude Code / Codex 修改後可能讓其他任務壞掉。

對策：

- baseline vs candidate comparison。
- regression tests。
- promotion policy。
- stable branch protection。

---

## 2. Command Risk Levels

### Low

- `ls`
- `pwd`
- `pytest`
- `npm test`
- `cat` 非敏感檔案
- `grep` 非敏感檔案

### Medium

- `npm run dev`
- `python script.py`
- 修改 workspace 檔案
- 套用 patch

### High

- install package
- delete file
- network request
- read hidden config
- change safety policy

### Forbidden

- read `.env`
- read SSH keys
- `sudo`
- `rm -rf`
- `curl | bash`
- exfiltrate data
