<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/>
          </svg>
        </div>
        <h1 class="logo-text">银行问数</h1>
        <span class="logo-sub">NL2SQL 智能查询</span>
      </div>

      <div class="sidebar-section">
        <div class="section-title">示例问题</div>
        <div
            v-for="(item, i) in sampleQuestions"
            :key="i"
            class="sample-item"
            @click="askSample(item.q)"
        >
          <span class="sample-tag" :class="item.tag">{{ item.tag }}</span>
          <span>{{ item.q }}</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="footer-badge">Powered by LangGraph</div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-area">
      <!-- 空状态欢迎页 -->
      <div v-if="messages.length === 0" class="welcome">
        <div class="welcome-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <h2>你好，我是银行数据助手</h2>
        <p>用自然语言提问，我将自动理解意图、生成 SQL 并返回查询结果</p>
        <div class="welcome-cards">
          <div v-for="(item, i) in sampleQuestions.slice(0, 4)" :key="i" class="welcome-card" @click="askSample(item.q)">
            <span class="card-tag" :class="item.tag">{{ item.tag }}</span>
            <span>{{ item.q }}</span>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="messagesEl" class="messages" v-else>
        <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message-row', msg.role]"
        >
          <!-- 助手头像 -->
          <div v-if="msg.role === 'assistant'" class="avatar assistant-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>

          <div class="bubble-container">
            <!-- 文本消息 -->
            <div v-if="msg.type === 'text'" class="bubble" :class="msg.role">
              {{ msg.content }}
            </div>

            <!-- 进度步骤 -->
            <div v-else-if="msg.type === 'steps'" class="bubble assistant steps-bubble">
              <div class="steps-header" @click="msg.collapsed = !msg.collapsed">
                <div class="steps-header-left">
                  <div class="steps-icon-wrap" :class="allStepsDone(msg) ? 'done' : 'running'">
                    <svg v-if="!allStepsDone(msg)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="steps-icon">
                      <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="steps-icon">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/>
                    </svg>
                  </div>
                  <span class="steps-title">{{ allStepsDone(msg) ? '分析完成' : '正在分析问题' }}</span>
                  <span class="steps-progress">{{ doneCount(msg) }}/{{ msg.steps.length }}</span>
                </div>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="collapse-arrow" :class="{ collapsed: msg.collapsed }">
                  <path d="M6 9l6 6 6-6"/>
                </svg>
              </div>
              <div class="steps" v-show="!msg.collapsed">
                <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="step" :class="{ 'step-done': step.status === 'success', 'step-error': step.status === 'error' }">
                  <div class="step-connector">
                    <div class="step-line" :class="{ 'line-active': sIdx < msg.steps.length - 1 }"></div>
                    <div class="step-dot" :class="step.status">
                      <svg v-if="step.status === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <path d="M5 13l4 4L19 7"/>
                      </svg>
                      <svg v-else-if="step.status === 'error'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <path d="M6 6l12 12M6 18L18 6"/>
                      </svg>
                      <div v-else class="pulse-ring"></div>
                    </div>
                  </div>
                  <div class="step-content">
                    <span class="step-text" :class="step.status">{{ step.label }}</span>
                    <span class="step-desc" v-if="step.desc">{{ step.desc }}</span>
                  </div>
                  <span class="step-badge" :class="step.status">
                    {{ step.status === 'success' ? '已完成' : step.status === 'error' ? '失败' : '处理中...' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 表格结果 -->
            <div v-else-if="msg.type === 'table'" class="bubble assistant table-bubble">
              <div class="table-header">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="table-icon">
                  <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/>
                </svg>
                <span>查询结果</span>
                <span class="row-count">{{ msg.rows.length }} 条记录</span>
              </div>
              <div class="table-wrap">
                <table class="result-table">
                  <thead>
                  <tr>
                    <th v-for="col in msg.columns" :key="col">{{ col }}</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="(row, rIdx) in msg.rows" :key="rIdx">
                    <td v-for="col in msg.columns" :key="col">{{ row[col] }}</td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 错误 -->
            <div v-else-if="msg.type === 'error'" class="bubble assistant error-bubble">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="error-icon">
                <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
              </svg>
              <span>{{ msg.content }}</span>
            </div>

            <!-- 消息时间 -->
            <div class="msg-time">{{ msg.time }}</div>
          </div>

          <!-- 用户头像 -->
          <div v-if="msg.role === 'user'" class="avatar user-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="input-wrapper">
        <div class="input-box">
          <input
              v-model="question"
              @keyup.enter="sendQuestion"
              :placeholder="loading ? '正在分析中...' : '输入你的问题，如：各分行的存款余额是多少？'"
              :disabled="loading"
          />
          <button @click="sendQuestion" :disabled="loading || !question.trim()">
            <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>
            </svg>
            <div v-else class="btn-spinner"></div>
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import {nextTick, ref} from "vue";

const API_URL = "/api/query";

const question = ref("");
const loading = ref(false);
const messages = ref([]);
const messagesEl = ref(null);

// 步骤文本映射：后端原始文本 -> 前端展示标签和描述
const stepMap = {
  "抽取关键字": { label: "理解问题意图", desc: "从自然语言中提取关键业务词" },
  "召回字段": { label: "匹配数据字段", desc: "在知识库中搜索相关数据表字段" },
  "召回指标": { label: "匹配业务指标", desc: "检索与问题相关的计算指标" },
  "召回字段取值": { label: "获取字段枚举值", desc: "查询字段的可选值用于精确匹配" },
  "合并召回信息": { label: "整合检索结果", desc: "合并字段与指标的召回信息" },
  "过滤指标信息": { label: "筛选有效指标", desc: "去除无关指标，保留核心指标" },
  "过滤表格": { label: "精简数据范围", desc: "确定需要查询的目标数据表" },
  "添加额外上下文": { label: "补充业务上下文", desc: "注入表结构与业务规则等背景信息" },
  "生成SQL": { label: "生成 SQL 语句", desc: "基于理解结果自动编写查询语句" },
  "验证SQL": { label: "校验 SQL 语法", desc: "检查语句正确性与执行安全性" },
  "执行SQL": { label: "执行查询", desc: "运行 SQL 并返回数据结果" },
};

const sampleQuestions = [
  { tag: "统计", q: "各分行本季度的存款余额" },
  { tag: "统计", q: "各风险等级客户的不良贷款率" },
  { tag: "趋势", q: "2025年各月存入金额变化趋势" },
  { tag: "对比", q: "对比手机银行和网上银行的转账金额" },
  { tag: "明细", q: "逾期超过90天的贷款明细" },
  { tag: "排名", q: "存款余额排名前3的网点" },
  { tag: "跨表", q: "当前存贷比是多少" },
  { tag: "画像", q: "白金客户的人均存款" },
];

function now() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function askSample(q) {
  question.value = q;
  sendQuestion();
}

function scrollToBottom() {
  const el = messagesEl.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

function allStepsDone(msg) {
  return msg.steps.length > 0 && msg.steps.every(s => s.status === "success" || s.status === "error");
}

function doneCount(msg) {
  return msg.steps.filter(s => s.status === "success").length;
}

function getStepMeta(rawText) {
  // 精确匹配
  if (stepMap[rawText]) return stepMap[rawText];
  // 模糊匹配
  for (const [key, val] of Object.entries(stepMap)) {
    if (rawText.includes(key) || key.includes(rawText)) return val;
  }
  return { label: rawText, desc: "" };
}

async function sendQuestion() {
  if (!question.value || loading.value) return;

  const q = question.value;
  question.value = "";
  loading.value = true;

  messages.value.push({role: "user", type: "text", content: q, time: now()});

  const stepIndex =
      messages.value.push({
        role: "assistant",
        type: "steps",
        steps: [],
        collapsed: false,
        time: now(),
      }) - 1;

  await nextTick();
  scrollToBottom();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({query: q}),
    });

    if (!response.body) throw new Error("服务器未返回流");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const {value, done} = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, {stream: true});
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const evt of events) {
        const line = evt.trim();
        if (!line.startsWith("data:")) continue;

        let data;
        try {
          data = JSON.parse(line.replace(/^data:\s*/, ""));
        } catch {
          continue;
        }

        const steps = messages.value[stepIndex].steps;

        if (data.type === "progress") {
          const meta = getStepMeta(data.step);
          let step = steps.find((s) => s.raw === data.step);
          if (!step) {
            step = { raw: data.step, label: meta.label, desc: meta.desc, status: data.status };
            steps.push(step);
          } else {
            step.status = data.status;
          }
        } else if (data.type === "result" && Array.isArray(data.data)) {
          messages.value[stepIndex].collapsed = true;
          messages.value.push({
            role: "assistant",
            type: "table",
            columns: Object.keys(data.data[0] || {}),
            rows: data.data,
            time: now(),
          });
        } else if (data.type === "error") {
          messages.value.push({
            role: "assistant",
            type: "error",
            content: data.message || "发生错误",
            time: now(),
          });
        }

        await nextTick();
        scrollToBottom();
      }
    }
  } catch (e) {
    messages.value.push({
      role: "assistant",
      type: "error",
      content: e?.message || "请求失败",
      time: now(),
    });
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
}
</script>

<style scoped>
/* ====== 全局重置 ====== */
:global(html), :global(body) {
  height: 100%;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

:global(body) {
  display: block !important;
  place-items: unset !important;
  background: #f0f2f5;
}

:global(#app) {
  height: 100%;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* ====== 布局 ====== */
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ====== 侧边栏 ====== */
.sidebar {
  width: 280px;
  min-width: 280px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 24px 0;
  overflow-y: auto;
}

.sidebar-header {
  padding: 0 24px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.logo-icon svg {
  width: 22px;
  height: 22px;
  color: #fff;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 1px;
}

.logo-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 4px;
  display: block;
}

.sidebar-section {
  flex: 1;
  padding: 20px 16px;
}

.section-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: rgba(255, 255, 255, 0.35);
  padding: 0 8px;
  margin-bottom: 12px;
  font-weight: 600;
}

.sample-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.2s;
  line-height: 1.4;
}

.sample-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.sample-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  opacity: 0.5;
}

.sample-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  flex-shrink: 0;
  letter-spacing: 0.5px;
}

.sample-tag.统计 { background: rgba(79, 172, 254, 0.2); color: #4facfe; }
.sample-tag.趋势 { background: rgba(255, 154, 0, 0.2); color: #ff9a00; }
.sample-tag.对比 { background: rgba(118, 75, 162, 0.2); color: #b37feb; }
.sample-tag.明细 { background: rgba(82, 196, 26, 0.2); color: #73d13d; }
.sample-tag.排名 { background: rgba(255, 77, 79, 0.2); color: #ff7875; }
.sample-tag.跨表 { background: rgba(19, 194, 194, 0.2); color: #13c2c2; }
.sample-tag.画像 { background: rgba(235, 47, 150, 0.2); color: #eb2f96; }

.sidebar-footer {
  padding: 16px 24px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.footer-badge {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.25);
  text-align: center;
}

/* ====== 主区域 ====== */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f7f8fa;
  position: relative;
  overflow: hidden;
}

/* ====== 欢迎页 ====== */
.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.welcome-icon {
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(79, 172, 254, 0.3);
}

.welcome-icon svg {
  width: 36px;
  height: 36px;
  color: #fff;
}

.welcome h2 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px;
}

.welcome p {
  font-size: 15px;
  color: #8c8c8c;
  margin: 0 0 36px;
}

.welcome-cards {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 700px;
}

.welcome-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
  max-width: 220px;
}

.welcome-card:hover {
  border-color: #4facfe;
  box-shadow: 0 4px 16px rgba(79, 172, 254, 0.15);
  transform: translateY(-2px);
}

.card-num {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.card-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}

.card-tag.统计 { background: #e6f7ff; color: #1890ff; }
.card-tag.趋势 { background: #fff7e6; color: #fa8c16; }
.card-tag.对比 { background: #f9f0ff; color: #722ed1; }
.card-tag.明细 { background: #f6ffed; color: #52c41a; }
.card-tag.排名 { background: #fff2f0; color: #ff4d4f; }
.card-tag.跨表 { background: #e6fffb; color: #13c2c2; }
.card-tag.画像 { background: #fff0f6; color: #eb2f96; }

/* ====== 消息区 ====== */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 40px 120px;
  scroll-behavior: smooth;
}

.message-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20px;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-row.user {
  justify-content: flex-end;
}

/* 头像 */
.avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar svg {
  width: 20px;
  height: 20px;
}

.assistant-avatar {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: #fff;
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);
}

.user-avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 气泡容器 */
.bubble-container {
  max-width: min(780px, 70%);
  margin: 0 14px;
}

/* 气泡 */
.bubble {
  padding: 14px 18px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  position: relative;
}

.bubble.user {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 16px rgba(79, 172, 254, 0.25);
}

.bubble.assistant {
  background: #fff;
  border: 1px solid #ebeef5;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

/* 消息时间 */
.msg-time {
  font-size: 11px;
  color: #bbb;
  margin-top: 6px;
  padding: 0 4px;
}

.message-row.user .msg-time {
  text-align: right;
}

/* ====== 步骤时间线 ====== */
.steps-bubble {
  padding: 0;
  overflow: hidden;
}

.steps-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #666;
  padding: 14px 20px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.steps-header:hover {
  background: #fafbfc;
}

.steps-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.steps-icon-wrap {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.steps-icon-wrap.running {
  background: linear-gradient(135deg, #e6f7ff, #bae7ff);
  animation: iconPulse 2s ease-in-out infinite;
}

.steps-icon-wrap.done {
  background: linear-gradient(135deg, #f6ffed, #d9f7be);
}

@keyframes iconPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(79, 172, 254, 0.2); }
  50% { box-shadow: 0 0 0 6px rgba(79, 172, 254, 0); }
}

.steps-icon {
  width: 16px;
  height: 16px;
}

.steps-icon-wrap.running .steps-icon {
  color: #1890ff;
}

.steps-icon-wrap.done .steps-icon {
  color: #52c41a;
}

.steps-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.steps-progress {
  font-size: 11px;
  font-weight: 500;
  color: #1890ff;
  background: #e6f7ff;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 4px;
}

.collapse-arrow {
  width: 18px;
  height: 18px;
  color: #bbb;
  transition: transform 0.3s ease;
  flex-shrink: 0;
}

.collapse-arrow.collapsed {
  transform: rotate(-90deg);
}

.steps {
  display: flex;
  flex-direction: column;
  padding: 4px 20px 16px 20px;
  border-top: 1px solid #f0f0f0;
  animation: stepsFadeIn 0.3s ease;
}

@keyframes stepsFadeIn {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 1000px; }
}

.step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  position: relative;
  animation: stepSlideIn 0.35s ease;
}

@keyframes stepSlideIn {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.step-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
  position: relative;
}

.step-line {
  width: 2px;
  height: 100%;
  background: #e8e8e8;
  position: absolute;
  top: 20px;
  left: 11px;
}

.step-line.line-active {
  background: linear-gradient(180deg, #b7eb8f 0%, #e8e8e8 100%);
}

.step:last-child .step-line {
  display: none;
}

.step-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.step-dot svg {
  width: 11px;
  height: 11px;
  color: #fff;
}

.step-dot.running {
  background: #fff;
  border: 2px solid #4facfe;
}

.step-dot.success {
  background: #52c41a;
  border: 2px solid #52c41a;
  box-shadow: 0 2px 8px rgba(82, 196, 26, 0.3);
}

.step-dot.error {
  background: #ff4d4f;
  border: 2px solid #ff4d4f;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.3);
}

.pulse-ring {
  width: 8px;
  height: 8px;
  background: #4facfe;
  border-radius: 50%;
  animation: pulseDot 1.5s ease-in-out infinite;
}

@keyframes pulseDot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(0.6); opacity: 0.5; }
}

.step-content {
  flex: 1;
  min-width: 0;
  padding-bottom: 14px;
}

.step-text {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  display: block;
  line-height: 1.4;
}

.step-text.success {
  color: #52c41a;
}

.step-text.error {
  color: #ff4d4f;
}

.step-desc {
  font-size: 12px;
  color: #999;
  display: block;
  margin-top: 2px;
  line-height: 1.4;
}

.step-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
  margin-top: 1px;
  white-space: nowrap;
}

.step-badge.running {
  background: #e6f7ff;
  color: #1890ff;
}

.step-badge.success {
  background: #f6ffed;
  color: #52c41a;
}

.step-badge.error {
  background: #fff2f0;
  color: #ff4d4f;
}

.step-done {
  opacity: 0.85;
}

.step-error {
  opacity: 1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ====== 表格 ====== */
.table-bubble {
  padding: 0;
  overflow: hidden;
}

.table-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
  font-weight: 600;
  color: #666;
}

.table-icon {
  width: 16px;
  height: 16px;
  color: #4facfe;
}

.row-count {
  margin-left: auto;
  font-size: 12px;
  color: #999;
  font-weight: 400;
  background: #f5f5f5;
  padding: 2px 10px;
  border-radius: 10px;
}

.table-wrap {
  max-width: 100%;
  overflow-x: auto;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
}

.result-table th,
.result-table td {
  padding: 10px 16px;
  text-align: left;
  font-size: 13px;
  white-space: nowrap;
}

.result-table th {
  background: #fafbfc;
  font-weight: 600;
  color: #555;
  border-bottom: 1px solid #ebeef5;
  position: sticky;
  top: 0;
}

.result-table td {
  color: #333;
  border-bottom: 1px solid #f5f5f5;
}

.result-table tbody tr:hover {
  background: #f5f7ff;
}

.result-table tbody tr:last-child td {
  border-bottom: none;
}

/* ====== 错误 ====== */
.error-bubble {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff2f0 !important;
  border-color: #ffccc7 !important;
  color: #cf1322;
}

.error-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #ff4d4f;
}

/* ====== 输入框 ====== */
.input-wrapper {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 40px 24px;
  background: linear-gradient(transparent, #f7f8fa 30%);
  pointer-events: none;
}

.input-box {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 8px 8px 20px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-box:focus-within {
  border-color: #4facfe;
  box-shadow: 0 4px 24px rgba(79, 172, 254, 0.15);
}

.input-box input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: #333;
  padding: 8px 0;
}

.input-box input::placeholder {
  color: #bbb;
}

.input-box button {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, box-shadow 0.15s;
  flex-shrink: 0;
}

.input-box button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(79, 172, 254, 0.4);
}

.input-box button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-box button svg {
  width: 18px;
  height: 18px;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ====== 滚动条美化 ====== */
.messages::-webkit-scrollbar {
  width: 6px;
}

.messages::-webkit-scrollbar-track {
  background: transparent;
}

.messages::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}
</style>
