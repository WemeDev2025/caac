<template>
  <div id="app">
    <h1>无人机题目关键词工具（{{ completedQuestionsCount }} / {{ totalQuestionsCount }} 已完成）</h1>
    
    <!-- 添加章节切换按钮 -->
    <div class="chapter-toggle">
      <button @click="toggleChapterGrid" class="toggle-button">
        {{ showChapterGrid ? '收起章节' : '选择章节' }}
        <span class="chapter-name"> Ch. {{ getCurrentChapterName }}</span>
      </button>
    </div>

    <!-- 使用 transition 组件包裹章节部分 -->
    <transition name="chapter-fade">
      <div class="chapter-section" v-if="showChapterGrid">
        <div class="overlay" @click="toggleChapterGrid"></div>
        <div class="chapter-grid">
          <div 
            v-for="(chapter, index) in chapters" 
            :key="chapter.id"
            class="chapter-item"
            :style="{ '--index': index }"
            :class="{ active: currentChapter === chapter.id }"
            @click="selectChapter(chapter.id)"
          >
            {{ chapter.name }}
          </div>
        </div>
      </div>
    </transition>

    <div class="container">
      <!-- 左侧：题目列表 -->
      <div class="question-list">
        <div v-if="isLoading">加载中...</div>
        <div
          v-else
          v-for="question in paginatedQuestions"
          :key="question.question_id"
          @click="loadQuestionDetail(question.question_id)"
          class="question-item"
          :class="{ 
            active: currentQuestion?.question_id === question.question_id,
            bold: hasCompleteKeywords(question) // 判断是否加粗
          }"
        >
          Q{{ question.question_id }}: {{ question.question_text }}
        </div>
      </div>

      <!-- 右侧：题目详情 -->
      <div class="question-detail" v-if="currentQuestion">
        <h3>题目 {{ currentQuestion.question_id }}</h3>
        <!-- 题目文本 -->
        <p 
          @mousedown="startSelection"
          @mousemove="updateSelection"
          @mouseup="endSelection"
          class="selectable-text"
        >
          {{ currentQuestion.question_text }}
        </p>
        <!-- 选项 -->
        <ul>
          <li
            v-for="(option, index) in currentQuestion.options"
            :key="index"
            @mousedown="startSelection"
            @mousemove="updateSelection"
            @mouseup="endSelection"
            class="selectable-text"
          >
            {{ option }}
          </li>
        </ul>
        <p>答案: {{ currentQuestion.answer }}</p>
        <!-- 关键词编辑 -->
        <div class="keyword-editor" v-if="filteredKeywords.length > 0">
          <ul>
            <li v-for="(keyword, index) in filteredKeywords" :key="index">
              <span :class="getKeywordClass(keyword.type)">
                {{ keyword.text }}
              </span>
              <button @click="removeKeyword(index)" class="delete-button">删除</button>
            </li>
          </ul>
        </div>

        <!-- 保存按钮 -->
        <button 
          @click="saveKeywords" 
          class="save-button"
        >
          下一题
        </button>
      </div>
    </div>

    <!-- 翻页按钮 -->
    <div class="pagination">
      <button 
        @click="prevPage" 
        :disabled="currentPage === 1"
      >
        上一页
      </button>
      <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
      <button 
        @click="nextPage" 
        :disabled="currentPage === totalPages"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      questions: [], // 题目列表
      currentQuestion: null, // 当前题目
      currentChapter: 1, // 当前章节
      chapters: [
        { id: 1, name: '概述' },
        { id: 2, name: '法律法规' },
        { id: 3, name: '空域' },
        { id: 4, name: '系统组成' },
        { id: 5, name: '飞行手册' },
        { id: 6, name: '任务规划' },
        { id: 7, name: '多旋翼动力飞控' },
        { id: 8, name: '多旋翼综合' },
        { id: 9, name: '气象(一)' },
        { id: 10, name: '气象(二)' },
        { id: 11, name: '飞行原理(一)' },
        { id: 12, name: '飞行原理(二)' },
        { id: 13, name: '飞行原理(三)' },
        { id: 14, name: '起降操纵(一)' },
        { id: 15, name: '起降操纵(二)' },
        { id: 16, name: '综合问答' }
      ],
      
      selectedKeywordType: 'question_text', // 默认关键词类型
      isLoading: false, // 加载状态
      currentPage: 1, // 当前页码
      pageSize: 10, // 每页显示的题目数量
      showChapterGrid: false, // 控制章节网格的显示/隐藏
      isSelecting: false, // 是否正在选择文本
      tempSelectedText: '', // 临时选中的文本
    };
  },
  computed: {
    // 计算已完成 keywords 标记的题目数量
    completedQuestionsCount() {
      return this.questions.filter(q =>
        q.keywords &&
        q.keywords.some(k => k.type === 'question_text' && k.text.trim() !== '') &&
        q.keywords.some(k => k.type === 'answer' && k.text.trim() !== '')
      ).length;
    },
    // 计算总题目数量
    totalQuestionsCount() {
      return this.questions.length;
    },
    // 过滤关键词，只显示题目文本和答案类型
    filteredKeywords() {
      return this.currentQuestion?.keywords?.filter(
        (k) => ['question_text', 'answer'].includes(k.type)
      ) || [];
    },
    // 获取当前页的题目列表
    paginatedQuestions() {
      // 先按章节过滤
      const filteredQuestions = this.questions.filter(q => q.chapter_id === this.currentChapter);
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return filteredQuestions.slice(start, end);
    },
    // 计算总页数
    totalPages() {
      const filteredQuestions = this.questions.filter(q => q.chapter_id === this.currentChapter);
      return Math.ceil(filteredQuestions.length / this.pageSize);
    },
    // 获取当前章节名称
    getCurrentChapterName() {
      const chapter = this.chapters.find(c => c.id === this.currentChapter);
      return chapter ? chapter.name : '';
    },
  },
  async created() {
    await this.fetchQuestions();
  },
  methods: {
    // 加载题目列表
    async fetchQuestions() {
      this.isLoading = true; // 开始加载
      try {
        const response = await fetch('http://localhost:5001/questions');
        if (!response.ok) throw new Error('加载题目列表失败');
        const data = await response.json();
        console.log('API 返回的数据:', data); // 打印数据到控制台

        // 提取 questions 数据
        if (data.length > 0 && data[0].questions) {
          this.questions = data[0].questions;
        } else {
          throw new Error('数据格式不正确');
        }
      } catch (error) {
        console.error(error);
        alert('加载题目列表失败，请稍后重试');
      } finally {
        this.isLoading = false; // 结束加载
      }
    },
    // 加载题目详情
    loadQuestionDetail(questionId) {
      if (!this.questions || !Array.isArray(this.questions)) {
        console.error("questions 未定义或不是数组");
        return;
      }

      // 直接查找匹配的题目
      this.currentQuestion = this.questions.find((q) => q.question_id === questionId);

      if (!this.currentQuestion) {
        console.error('题目详情未找到');
        alert('题目详情未找到');
        return;
      }

      // 初始化 keywords 数组（如果不存在）
      if (!this.currentQuestion.keywords) {
        this.currentQuestion.keywords = [];
      } else {
        // 清理无效关键词
        this.currentQuestion.keywords = this.currentQuestion.keywords.filter(
          (keyword) => keyword.text && keyword.text.trim() !== '' && ['question_text', 'answer'].includes(keyword.type)
        );
      }

      console.log("加载的题目详情:", this.currentQuestion);
    },
    // 开始选择文本
    startSelection() {
      this.isSelecting = true;
      this.tempSelectedText = '';
      
      // 清除当前页面的所有选择
      window.getSelection().removeAllRanges();
    },

    // 更新选择的文本
    updateSelection() {
      if (!this.isSelecting) return;
      
      const selection = window.getSelection();
      selection.modify('extend', 'forward', 'character');
      
      this.tempSelectedText = selection.toString().trim();
    },

    // 结束选择文本
    endSelection() {
      if (!this.isSelecting) return;
      this.isSelecting = false;

      const selection = window.getSelection();
      const selectedText = selection.toString().trim();

      if (!selectedText) return;

      // 检查选中的文本是否属于题目文本
      const isQuestionText = this.currentQuestion.question_text.includes(selectedText);

      // 检查选中的文本是否属于正确答案的选项内容
      const correctOptionIndex = this.currentQuestion.answer.charCodeAt(0) - 65;
      const correctOptionContent = this.currentQuestion.options[correctOptionIndex];
      const isCorrectAnswerContent = correctOptionContent.includes(selectedText);

      // 如果选中的文本既不属于题目文本，也不属于正确答案的选项内容，则提示错误
      if (!isQuestionText && !isCorrectAnswerContent) {
        console.warn('禁止在错误答案上添加关键词:', selectedText);
        alert('只能在题目文本或正确答案上添加关键词！');
        return;
      }

      // 检查是否已存在相同的关键词
      const isDuplicate = this.currentQuestion.keywords.some(
        (keyword) => keyword.text === selectedText
      );

      if (isDuplicate) {
        alert('该关键词已存在！');
        return;
      }

      // 确定关键词类型
      const keywordType = isCorrectAnswerContent ? 'answer' : 'question_text';

      // 添加关键词
      this.currentQuestion.keywords.push({
        text: selectedText,
        type: keywordType,
      });

      // 清除选择
      selection.removeAllRanges();
    },
    // 删除关键词
    removeKeyword(index) {
      this.currentQuestion.keywords.splice(index, 1);
    },
    // 保存关键词
    async saveKeywords() {
      // 防止重复点击逻辑已移除，按钮状态不再变化

      try {
        const questionId = Number(this.currentQuestion.question_id);
        console.log('questionId:', questionId); // 打印 questionId
        if (isNaN(questionId)) {
          throw new Error('question_id 不是有效的数字');
        }

        // 过滤掉 text 为空和 type 不合法的关键词
        const validKeywords = this.currentQuestion.keywords.filter(
          (keyword) => keyword.text && keyword.text.trim() !== '' && ['question_text', 'answer'].includes(keyword.type)
        );

        console.log('validKeywords:', JSON.stringify(validKeywords, null, 2)); // 打印过滤后的 keywords
      

        if (!Array.isArray(validKeywords)) {
          throw new Error('keywords 不是有效的数组');
        }

        // 检查每个关键词对象是否包含 text 和 type 字段
        const isValidKeywords = validKeywords.every(
          (keyword) => {
            const hasText = keyword.text && typeof keyword.text === 'string';
            const hasType = keyword.type && typeof keyword.type === 'string';
            return hasText && hasType;
          }
        );

        if (!isValidKeywords) {
          throw new Error('keywords 数组中的元素格式不正确');
        }

        const response = await fetch(
          `http://localhost:5001/questions/${questionId}/keywords`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(validKeywords), // 发送过滤后的 keywords
          }
        );

        if (!response.ok) {
          const errorData = await response.json(); // 解析错误信息
          throw new Error(errorData.error || '保存失败');
        }

        // alert('保存成功！');
        console.log('保存成功');
        // 获取当前题目的索引
        const currentIndex = this.questions.findIndex(q => q.question_id === this.currentQuestion.question_id);
        if (currentIndex !== -1 && currentIndex < this.questions.length - 1) {
          // 切换到下一题
          this.loadQuestionDetail(this.questions[currentIndex + 1].question_id);
        } else {
          console.log("已到达最后一题，无法切换");
        }
      } catch (error) {
        console.error('保存失败:', error);
        alert(`保存失败: ${error.message}`);
      }
    },
    // 获取关键词高亮样式
    getKeywordClass(type) {
      return {
        highlight: type === 'question_text',
        'highlight-answer': type === 'answer',
      };
    },
    // 判断题目是否包含完整的关键词（question_text 和 answer）
    hasCompleteKeywords(question) {
      if (!question.keywords || !Array.isArray(question.keywords)) return false;

      const hasQuestionText = question.keywords.some(
        (keyword) => keyword.type === 'question_text' && keyword.text && keyword.text.trim() !== ''
      );
      const hasAnswer = question.keywords.some(
        (keyword) => keyword.type === 'answer' && keyword.text && keyword.text.trim() !== ''
      );

      return hasQuestionText && hasAnswer;
    },
    // 上一页
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    // 下一页
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
    // 切换章节网格显示/隐藏
    toggleChapterGrid() {
      this.showChapterGrid = !this.showChapterGrid;
    },
    // 修改章节选择方法
    selectChapter(chapterId) {
      this.currentChapter = chapterId;
      this.currentPage = 1;
      this.showChapterGrid = false; // 选择后自动收起
    },
  },
};
</script>

<style scoped>
/* 添加全局样式 */
:root {
  margin: 0;
  padding: 0;
  overflow: hidden;
}

#app {
  font-family: Arial, sans-serif;
  padding: 0;
  margin: 0;
  min-height: 100vh;
  background: linear-gradient(to bottom, #264C80, #082348);
  color: rgb(255, 255, 255);
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
}

h1 {
  margin-left: 600px;
  padding: 20px;
}

.container {
  display: flex;
  gap: 20px;
  position: relative;
  height: calc(100vh - 200px);
  padding: 20px;
  padding-top: 0;
  max-width: 1400px;
  margin: 0 auto;
}

.question-list {
  flex: 1;
  min-width: 300px;
  padding: 20px;
  padding-top: 0;
  padding-left: 20px; /* 确保与章节按钮对齐 */
  overflow-y: auto;
  max-height: calc(100vh - 140px);
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.question-list::-webkit-scrollbar {
  display: none; /* Chrome, Safari and Opera */
}

.question-item {
  padding: 10px;
  margin: 5px 0;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
  color: rgb(231, 231, 231);
}

.question-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.question-item.active {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.question-item.bold {
  color: #00ff9d; /* 使用亮绿色文字 */
  font-weight: 500; /* 稍微加粗一点 */
  text-shadow: 0 0 8px rgba(0, 255, 157, 0.3); /* 添加轻微发光效果 */
}

.question-detail {
  flex: 1.2;
  min-width: 400px;
  max-width: 800px;
  padding: 30px;
  padding-top: 25px;
  overflow-y: auto;
  max-height: calc(80vh - 140px); /* 调整高度 */
  scrollbar-width: none;
  -ms-overflow-style: none;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 4px 24px -1px rgba(0, 0, 0, 0.2),
    0 1px 3px rgba(255, 255, 255, 0.05);
  margin: 0 auto;
  margin-top: -45px;
}

.question-detail h3 {
  margin-top: 0;
  margin-bottom: 30px; /* 增加标题下方间距 */
  color: rgba(255, 255, 255, 0.95);
  font-weight: 500;
  letter-spacing: 0.5px; /* 增加字间距 */
  font-size: 20px; /* 调整字体大小 */
  padding-bottom: 15px; /* 添加底部内边距 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.1); /* 添加底部分隔线 */
}

.question-detail p,
.question-detail ul {
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
}

.question-detail ul {
  padding-left: 20px;
  margin: 15px 0;
}

.question-detail li {
  margin: 8px 0;
}

/* 调整关键词编辑区域样式 */
.keyword-editor {
  margin-top: 20px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 15px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.keyword-editor ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.keyword-editor li {
  display: flex;
  align-items: center;
  justify-content: space-between; /* 将内容分散到两端 */
  gap: 10px;
  margin: 8px 0;
  padding: 8px 12px;
  background: rgba(0, 255, 157, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 157, 0.2);
  transition: all 0.2s ease;
}

.keyword-editor li:hover {
  background: rgba(0, 255, 157, 0.15);
  border-color: rgba(0, 255, 157, 0.3);
}

/* 修改高亮样式以适应深色背景 */
.highlight {
  background-color: rgba(255, 235, 59, 0.9);
  color: rgba(0, 0, 0, 0.9);
  padding: 2px 6px;
  border-radius: 4px;
  margin: 0 2px;
}

.highlight-answer {
  background-color: rgba(165, 214, 167, 0.9);
  color: rgba(0, 0, 0, 0.9);
  padding: 2px 6px;
  border-radius: 4px;
  margin: 0 2px;
}

.delete-button {
  background-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: 400px; /* 将按钮推到右侧 */
  min-width: 60px; /* 设置最小宽度保持一致性 */
  text-align: center; /* 文字居中 */
}

.delete-button:hover {
  background-color: rgba(255, 36, 36, 0.2);
  border-color: rgba(255, 36, 36, 0.3);
  color: rgb(255, 36, 36);
}

.pagination {
  position: fixed;
  bottom: 30px; /* 增加底部间距 */
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 50px;
  background-color: rgba(0, 0, 0, 0.7);
  padding: 10px;
  border-radius: 8px;
  z-index: 100; /* 确保在其他元素之上 */
}

.pagination button {
  padding: 8px 16px;
  background-color: #039d62;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.pagination button:disabled {
  background-color: #434343;
  cursor: not-allowed;
}

.pagination span {
  color: white;
}

.save-button {
  position: absolute;
  bottom: 570px;
  right: 30px;
  padding: 8px 20px;
  background: rgba(3, 157, 98, 0.9);
  color: white;
  border: 1px solid rgba(3, 157, 98, 0.3);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.1),
    0 1px 2px rgba(3, 157, 98, 0.1);
}

.save-button:disabled {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
/* 章节切换按钮样式 */
.chapter-toggle {
  padding: 10px 20px;
  display: flex;
  justify-content: flex-start;
  margin-left: 50px; /* 与题目列表左侧对齐 */
}

.toggle-button {
  width: 14%;
  margin-left: 149px; /* 设置左边距为149px */
  background: rgba(32, 32, 32, 0.935);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 144, 137, 0.15);
  color: white;
  border-radius: 6px;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 28px;
  font-size: 13px;
  justify-content: flex-start;
  box-shadow: 
    0 1px 3px rgba(0, 0, 0, 0.1),
    0 1px 2px rgba(255, 255, 255, 0.05);
  font-weight: 500;
  letter-spacing: 0.3px;
  white-space: nowrap;
  overflow: hidden;
}

.toggle-button:hover {
  background: rgba(0, 0, 0, 0.644);
  transform: translateY(-1px);
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.15),
    0 1px 3px rgba(255, 255, 255, 0.1);
}

.toggle-button:active {
  transform: translateY(0px);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.1),
    0 1px 1px rgba(255, 255, 255, 0.05);
}

.chapter-name {
  color: rgba(255, 255, 255, 0.9);
  margin-left: 1px;
  padding-left: 10px;
  border-left: 2px solid rgba(255, 255, 255, 0.2);
  font-weight: 400;
}

/* 章节部分容器 */
.chapter-section {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  pointer-events: none; /* 允许点击穿透到底层 */
}

/* 遮罩层样式 */
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.9);
  z-index: 1001;
  transition: opacity 0.3s ease;
}

/* 添加过渡动画样式 */
.chapter-fade-enter-active,
.chapter-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.chapter-fade-enter-from,
.chapter-fade-leave-to {
  opacity: 0;
}

/* 修改章节网格样式 */
.chapter-grid {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1002;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 20px;
  width: 80%;
  max-width: 1200px;
  background-color: rgba(0, 0, 0, 0.4);
  border-radius: 8px;
  pointer-events: auto;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.chapter-fade-leave-active .chapter-grid {
  transform: translate(-50%, -50%) scale(0.95);
  opacity: 0;
}

.chapter-item {
  background-color: rgba(255, 255, 255, 0.1);
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  color: white;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60px;
  pointer-events: auto;
}

.chapter-fade-leave-active .chapter-item {
  transition-delay: calc((15 - var(--index)) * 0.03s);
  transform: translateY(10px);
  opacity: 0;
}

.chapter-item:hover {
  background-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.chapter-item.active {
  background-color: #039d62;
  box-shadow: 0 4px 12px rgba(3, 157, 98, 0.3);
}

/* 可选择文本的样式 */
.selectable-text {
  user-select: text;
  cursor: text;
  position: relative;
}

/* 选中文本的样式 */
.selectable-text::selection {
  background-color: rgba(0, 255, 157, 0.3);
  color: white;
  text-shadow: 0 0 8px rgba(0, 255, 157, 0.5);
}

/* 添加按钮容器样式 */
.button-group {
  display: flex;
  gap: 10px; /* 按钮之间的间距 */
  align-items: center;
}
</style>