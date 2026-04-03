const result = document.getElementById("result");
const form = document.getElementById("review-form");
const indexButton = document.getElementById("index-btn");

async function callApi(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(JSON.stringify(data, null, 2));
  }
  return data;
}

function renderProgress(steps, currentStepIndex) {
  let html = '';
  for (let i = 0; i < steps.length; i++) {
    if (i < currentStepIndex) {
      html += `✅ ${steps[i]} 완료\n`;
    } else if (i === currentStepIndex) {
      html += `🔄 ${steps[i]} (진행 중...)\n`;
    } else {
      html += `⏳ ${steps[i]} 대기 중...\n`;
    }
  }
  return html;
}

// 리뷰 데이터를 브라우저에 랜더링 (미리보기)
function renderReviewPreview(data) {
  let html = `<div style="font-family: inherit;">`;
  html += `<h3 style="color:var(--primary)">📋 요약 (Summary)</h3><p>${data.summary}</p>`;

  if (data.findings && data.findings.length > 0) {
    html += `<h3 style="color:var(--primary); margin-top:24px;">🔍 발견된 이슈 (Findings)</h3>`;
    data.findings.forEach(f => {
      html += `<div style="background: rgba(255,255,255,0.05); padding: 16px; margin-bottom: 12px; border-radius: 8px; border-left: 4px solid var(--secondary);">`;
      html += `<strong>[${f.severity.toUpperCase()}] ${f.title}</strong><br/>`;
      html += `<small style="color:var(--text-muted)">파일: <code>${f.file_path}</code> (Line ${f.line})</small><br/><br/>`;
      html += `<strong>상세 원인:</strong> ${f.rationale}<br/>`;
      html += `<strong>권장 사항:</strong> ${f.recommendation}`;
      html += `</div>`;
    });
  }

  if (data.improved_code && data.improved_code.length > 0) {
    html += `<h3 style="color:var(--primary); margin-top:24px;">💡 개선된 코드 (Improved Code)</h3>`;
    data.improved_code.forEach(c => {
      html += `<div style="background: rgba(255,255,255,0.05); padding: 16px; margin-bottom: 12px; border-radius: 8px;">`;
      html += `<strong>대상:</strong> <code>${c.symbol}</code> <span style="color:var(--text-muted)">(${c.file_path})</span><br/>`;
      html += `<strong>설명:</strong> ${c.explanation}<br/><br/>`;
      html += `<pre style="background: rgba(0,0,0,0.5); padding: 12px; border-radius: 6px;"><code>${c.code.replace(/</g, '&lt;')}</code></pre>`;
      html += `</div>`;
    });
  }

  html += `</div>`;
  return html;
}

// 리뷰 데이터를 마크다운 파일로 변환
function generateMarkdown(data) {
  let md = `# AI 코드 리뷰 보고서\n\n`;
  md += `## 📋 요약\n${data.summary}\n\n`;

  if (data.findings && data.findings.length > 0) {
    md += `## 🔍 발견된 이슈\n\n`;
    data.findings.forEach(f => {
      md += `### [${f.severity.toUpperCase()}] ${f.title}\n`;
      md += `- **위치**: \`${f.file_path}:${f.line}\`\n`;
      md += `- **원인**: ${f.rationale}\n`;
      md += `- **권장**: ${f.recommendation}\n\n`;
    });
  }

  if (data.improved_code && data.improved_code.length > 0) {
    md += `## 💡 개선된 코드\n\n`;
    data.improved_code.forEach(c => {
      md += `### 대상: \`${c.symbol}\` (${c.file_path})\n`;
      md += `**설명**: ${c.explanation}\n\n`;
      md += `\`\`\`python\n${c.code}\n\`\`\`\n\n`;
    });
  }
  return md;
}

// 파일 다운로드 트리거 함수
function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type: type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

indexButton.addEventListener("click", async () => {
  const githubUrl = document.getElementById("github_url").value;
  if (!githubUrl) {
    alert("GitHub 저장소 URL을 입력해주세요!");
    return;
  }

  const steps = [
    "GitHub 저장소 연결 및 코드 복제",
    "Python 파일 스캔 및 구조 분석",
    "AST 기반 코드 단위(Chunk) 분할",
    "Qdrant 벡터 데이터베이스 임베딩 저장"
  ];

  let currentStep = 0;
  result.textContent = renderProgress(steps, currentStep);

  const progressInterval = setInterval(() => {
    if (currentStep < steps.length - 1) {
      currentStep++;
      result.textContent = renderProgress(steps, currentStep);
    }
  }, 1500);

  try {
    const data = await callApi("/api/index", { github_url: githubUrl, branch: "main" });
    clearInterval(progressInterval);

    let finalHtml = "✨ <strong>[인덱싱 완료]</strong>\n\n" + JSON.stringify(data, null, 2);
    result.innerHTML = `<pre>${finalHtml}</pre>`;
  } catch (error) {
    clearInterval(progressInterval);
    result.textContent += "\n\n❌ 오류 발생:\n" + error.message;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const githubUrl = document.getElementById("github_url").value;
  const question = document.getElementById("question").value;

  if (!githubUrl || !question) {
    alert("URL과 질문을 모두 입력해주세요!");
    return;
  }

  const payload = {
    github_url: githubUrl,
    question: question,
  };

  const steps = [
    "저장소 컨텍스트 및 질문 분석",
    "관련 코드 청크 검색 (RAG 수행)",
    "LLM 리뷰 프롬프트 생성",
    "AI 코드 퀄리티 분석 보고서 작성"
  ];

  let currentStep = 0;
  result.textContent = renderProgress(steps, currentStep);

  const progressInterval = setInterval(() => {
    if (currentStep < steps.length - 1) {
      currentStep++;
      result.textContent = renderProgress(steps, currentStep);
    }
  }, 2000);

  try {
    const data = await callApi("/api/review", payload);
    clearInterval(progressInterval);

    // 미리보기 랜더링
    result.innerHTML = `✨ <strong style="color:var(--primary); font-size:1.2rem;">[리뷰 분석 완료]</strong><br/><br/>` + renderReviewPreview(data);

    // 다운로드 버튼 컨테이너 활성화 및 핸들러 바인딩
    const downloadActions = document.getElementById("download-actions");
    downloadActions.style.display = "flex";

    document.getElementById("btn-download-md").onclick = () => downloadFile(generateMarkdown(data), "ai_code_review.md", "text/markdown");
    document.getElementById("btn-download-json").onclick = () => downloadFile(JSON.stringify(data, null, 2), "ai_code_review.json", "application/json");

  } catch (error) {
    clearInterval(progressInterval);
    result.textContent += "\n\n❌ 오류 발생:\n" + error.message;
  }
});
